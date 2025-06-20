import os
import sys
import schedule
import time
import logging
import glob
import json
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Importa os módulos do projeto
from src.market_data_collector import MarketDataCollector
from src.utils.email_sender import EmailSender

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_email_scheduler.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MarketEmailScheduler:
    def __init__(self):
        self.collector = MarketDataCollector()
        self.email_sender = EmailSender()
        self.logger = logging.getLogger(__name__)
        
        # Cria pasta para os JSONs se não existir
        self.json_folder = "market_data_files"
        if not os.path.exists(self.json_folder):
            os.makedirs(self.json_folder)
            self.logger.info(f"[FOLDER] Pasta criada: {self.json_folder}")
        
    def collect_and_send_email(self):
        """Coleta dados e envia por email"""
        try:
            self.logger.info("=== Iniciando coleta de dados de mercado ===")
            
            # Coleta os dados
            market_data = self.collector.collect_market_data()
            
            # Gera nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"market_data_{timestamp}.json"
            filepath = os.path.join(self.json_folder, filename)
            
            # Salva os dados localmente
            self.collector.save_to_file(market_data, filepath)
            self.logger.info(f"[FILE] Dados salvos em: {filepath}")
            
            # Limpa arquivos antigos, mantendo apenas os 15 mais recentes
            self.cleanup_old_files()
            
            # Gera JSON consolidado com todos os dados
            consolidated_file = self.generate_consolidated_json()
            
            # Envia por email apenas com o arquivo consolidado
            success = self.email_sender.send_market_data(market_data, attach_json=False, json_folder=None, consolidated_file=consolidated_file)
            
            if success:
                self.logger.info("[OK] Email enviado com sucesso!")
                # Log resumo
                price = market_data['current_price']
                self.logger.info(f"[PRICE] Preço BTC: ${price:,.2f}")
                if 'liquidations' in market_data:
                    total_liqs = market_data['liquidations']['total_liqs_24h']
                    self.logger.info(f"[LIQ] Liquidações 24h: ${total_liqs:,.2f}")
            else:
                self.logger.error("[ERROR] Falha ao enviar email")
                
        except Exception as e:
            self.logger.error(f"[ERROR] Erro na coleta/envio: {str(e)}")
    
    def cleanup_old_files(self):
        """Remove arquivos antigos, mantendo apenas os 15 mais recentes"""
        try:
            # Busca APENAS os arquivos JSON individuais (exclui consolidados)
            json_files = glob.glob(os.path.join(self.json_folder, "market_data_2*.json"))  # Só pega os com timestamp
            
            # Ordena por data de modificação (mais recente primeiro)
            json_files.sort(key=os.path.getmtime, reverse=True)
            
            # Remove arquivos além dos 15 mais recentes
            files_to_delete = json_files[15:]  # Mantém apenas os 15 primeiros
            
            for file_path in files_to_delete:
                os.remove(file_path)
                filename = os.path.basename(file_path)
                self.logger.info(f"[DEL] Arquivo removido: {filename}")
                
            if files_to_delete:
                self.logger.info(f"[CLEAN] Limpeza concluída. {len(files_to_delete)} arquivo(s) removido(s)")
            
            # Log do total de arquivos mantidos
            remaining_files = len(json_files) - len(files_to_delete)
            self.logger.info(f"[KEEP] Total de arquivos mantidos: {remaining_files}")
                
        except Exception as e:
            self.logger.error(f"[ERROR] Erro na limpeza de arquivos: {str(e)}")
    
    def generate_consolidated_json(self):
        """Gera JSON consolidado otimizado para análise de IA"""
        try:
            # Remove arquivo consolidado antigo se existir
            old_consolidated = os.path.join(self.json_folder, "market_data_consolidated_for_ai.json")
            if os.path.exists(old_consolidated):
                os.remove(old_consolidated)
                self.logger.info("[DEL] Arquivo consolidado antigo removido")
            
            # Busca APENAS os arquivos JSON individuais (exclui consolidados)
            json_files = glob.glob(os.path.join(self.json_folder, "market_data_2*.json"))  # Só pega os com timestamp
            
            # Ordena por data de modificação (mais recente primeiro)
            json_files.sort(key=os.path.getmtime, reverse=True)
            
            # Pega apenas os 15 mais recentes
            json_files = json_files[:15]
            
            # Estrutura otimizada para IA com novos campos
            consolidated_data = {
                "ai_analysis_metadata": {
                    "description": "Dados históricos de Bitcoin para análise técnica profissional",
                    "data_source": "Binance Futures API",
                    "consolidated_at": datetime.now().isoformat(),
                    "total_snapshots": len(json_files),
                    "time_interval_minutes": 2,
                    "data_points_explanation": "Cada snapshot representa uma coleta completa de dados de mercado com indicadores avançados",
                    "new_features": [
                        "VWAP em múltiplos timeframes (1h, 4h, diário)",
                        "Delta Volume absoluto e cumulativo para análise de fluxo",
                        "Imbalance Score baseado na posição no spread",
                        "Histórico de Funding Rate (últimos 3 valores)",
                        "Flags de Absorção em velas de 15m",
                        "Volume Profile 4h com POC, VAH, VAL",
                        "Clusters de liquidação estimados",
                        "Indicadores técnicos avançados"
                    ],
                    "analysis_suggestions": [
                        "Compare VWAP entre timeframes para identificar tendências",
                        "Use delta volume cumulativo para detectar divergências",
                        "Monitore imbalance_score para timing de entrada/saída",
                        "Observe flags de absorção para identificar reversões",
                        "Analise volume profile para suporte/resistência dinâmicos",
                        "Use funding_history para identificar extremos de sentiment",
                        "Correlacione clusters de liquidação com movimentos de preço"
                    ]
                },
                "market_snapshots": []
            }
            
            # Carrega e organiza dados de cada arquivo
            snapshot_counter = 1
            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extrai timestamp do nome do arquivo
                    file_timestamp = os.path.basename(file_path).replace('market_data_', '').replace('.json', '')
                    
                    # Estrutura cada snapshot de forma clara com novos campos
                    snapshot = {
                        "snapshot_info": {
                            "sequence_number": snapshot_counter,
                            "file_timestamp": file_timestamp,
                            "collection_time": data.get('timestamp', ''),
                            "data_age_minutes": (snapshot_counter - 1) * 2,
                            "is_most_recent": snapshot_counter == 1
                        },
                        "price_data": {
                            "current_price_usdt": data.get('current_price', 0),
                            "price_change_24h_percent": data.get('price_change_24h', 0),
                            "high_24h": data.get('high_24h', 0),
                            "low_24h": data.get('low_24h', 0)
                        },
                        # NOVO: VWAP em múltiplos timeframes
                        "vwap_analysis": data.get('vwap', {
                            "1h": 0,
                            "4h": 0,
                            "d": 0
                        }),
                        "volume_data": {
                            "volume_24h_usdt": data.get('stats', {}).get('volume_24h', 0),
                            "taker_buy_volume_24h": data.get('stats', {}).get('taker_buy_vol_24h', 0),
                            "taker_sell_volume_24h": data.get('stats', {}).get('taker_sell_vol_24h', 0),
                            "buy_sell_ratio": data.get('stats', {}).get('taker_buy_vol_24h', 0) / max(data.get('stats', {}).get('taker_sell_vol_24h', 1), 1)
                        },
                        # NOVO: Flow analysis com delta volume
                        "flow_analysis": {
                            "delta_volume_absolute": data.get('flow', {}).get('delta_volume_absolute', 0),
                            "delta_volume_cumulative": data.get('flow', {}).get('delta_volume_cumulative', []),
                            "perp_cvd": data.get('flow', {}).get('perp_cvd', 0),
                            "spot_cvd": data.get('flow', {}).get('spot_cvd', 0)
                        },
                        "derivatives_data": {
                            "open_interest_usd": data.get('derivatives', {}).get('open_interest_usd', 0),
                            "open_interest_btc": data.get('derivatives', {}).get('open_interest_coin', 0),
                            "oi_change_4h_percent": data.get('derivatives', {}).get('oi_change_4h_pct', 0),
                            "funding_rate_percent": data.get('derivatives', {}).get('funding_rate', 0) * 100,
                            "next_funding_time": data.get('derivatives', {}).get('funding_next', ''),
                            # NOVO: Histórico de funding
                            "funding_history": data.get('derivatives', {}).get('funding_history', [])
                        },
                        "liquidations_data": {
                            **data.get('liquidations', {
                                "long_liquidations_24h": 0,
                                "short_liquidations_24h": 0,
                                "total_liquidations_24h": 0
                            }),
                            # NOVO: Clusters de liquidação
                            "liquidations_clusters": data.get('liquidations', {}).get('liquidations_clusters', [])
                        },
                        "order_book_analysis": {
                            "bid_ask_spread": data.get('order_book', {}).get('spread', 0),
                            "imbalance_percent": data.get('order_book', {}).get('imbalance_pct', 0),
                            # NOVO: Imbalance score
                            "imbalance_score": data.get('order_book', {}).get('imbalance_score', 0),
                            "market_pressure": "bullish" if data.get('order_book', {}).get('imbalance_score', 0) > 0.3 else "bearish" if data.get('order_book', {}).get('imbalance_score', 0) < -0.3 else "neutral",
                            "depth_analysis": data.get('order_book', {}).get('depth_pct', {})
                        },
                        # MELHORADO: Indicadores técnicos de múltiplos timeframes
                        "technical_indicators": {
                            "15m": data.get('timeframes', {}).get('15m', {}).get('indicators', {}),
                            "1h": data.get('timeframes', {}).get('1h', {}).get('indicators', {}),
                            "4h": data.get('timeframes', {}).get('4h', {}).get('indicators', {}),
                            "advanced_1h": data.get('timeframes', {}).get('1h', {}).get('indicators', {}).get('advanced', {})
                        },
                        # NOVO: Volume Profile 4h
                        "volume_profile_4h": data.get('timeframes', {}).get('4h', {}).get('volume_profile_4h', {
                            "poc": 0,
                            "vah": 0,
                            "val": 0
                        }),
                        # NOVO: Flags de absorção (apenas para 15m)
                        "absorption_flags_15m": {
                            "detected_absorption_candles": len([
                                c for c in data.get('timeframes', {}).get('15m', {}).get('candles', [])
                                if isinstance(c, dict) and c.get('absorcao', False)
                            ]),
                            "last_5_candles_absorption": [
                                c.get('absorcao', False) for c in data.get('timeframes', {}).get('15m', {}).get('candles', [])[-5:]
                                if isinstance(c, dict)
                            ]
                        },
                        "raw_data_reference": {
                            "note": "Este snapshot contém todos os dados originais da API com novos campos implementados",
                            "full_data": data
                        }
                    }
                    
                    consolidated_data["market_snapshots"].append(snapshot)
                    snapshot_counter += 1
                    
                except Exception as e:
                    self.logger.error(f"[ERROR] Erro ao processar arquivo {file_path}: {str(e)}")
                    continue
            
            # Adiciona análise de tendências expandida com novos campos
            if len(consolidated_data["market_snapshots"]) >= 2:
                recent_snapshot = consolidated_data["market_snapshots"][0]
                oldest_snapshot = consolidated_data["market_snapshots"][-1]
                
                recent_price = recent_snapshot["price_data"]["current_price_usdt"]
                oldest_price = oldest_snapshot["price_data"]["current_price_usdt"]
                price_trend = ((recent_price - oldest_price) / oldest_price) * 100 if oldest_price > 0 else 0
                
                # Análise de delta volume
                recent_delta = recent_snapshot["flow_analysis"]["delta_volume_absolute"]
                delta_cumulative = recent_snapshot["flow_analysis"]["delta_volume_cumulative"]
                delta_trend = "bullish" if recent_delta > 0 else "bearish" if recent_delta < 0 else "neutral"
                
                # Análise de funding
                funding_history = recent_snapshot["derivatives_data"]["funding_history"]
                funding_trend = "increasing" if len(funding_history) >= 2 and funding_history[-1] > funding_history[-2] else "decreasing" if len(funding_history) >= 2 and funding_history[-1] < funding_history[-2] else "stable"
                
                # Análise de imbalance
                recent_imbalance = recent_snapshot["order_book_analysis"]["imbalance_score"]
                imbalance_pressure = recent_snapshot["order_book_analysis"]["market_pressure"]
                
                # Análise de absorção
                absorption_count = recent_snapshot["absorption_flags_15m"]["detected_absorption_candles"]
                
                consolidated_data["ai_analysis_metadata"]["quick_insights"] = {
                    "price_analysis": {
                        "price_trend_percent": round(price_trend, 4),
                        "trend_direction": "upward" if price_trend > 0 else "downward" if price_trend < 0 else "sideways",
                        "most_recent_price": recent_price,
                        "oldest_price_in_dataset": oldest_price
                    },
                    "flow_analysis": {
                        "current_delta_volume": recent_delta,
                        "delta_trend": delta_trend,
                        "cumulative_data_points": len(delta_cumulative)
                    },
                    "market_structure": {
                        "funding_trend": funding_trend,
                        "current_funding_rate": funding_history[-1] if funding_history else 0,
                        "order_book_imbalance_score": recent_imbalance,
                        "market_pressure": imbalance_pressure
                    },
                    "absorption_activity": {
                        "total_absorption_candles": absorption_count,
                        "absorption_detected": absorption_count > 0
                    },
                    "dataset_info": {
                        "data_timespan_minutes": len(consolidated_data["market_snapshots"]) * 2,
                        "vwap_available": bool(recent_snapshot["vwap_analysis"]["1h"]),
                        "volume_profile_available": bool(recent_snapshot["volume_profile_4h"]["poc"])
                    }
                }
            
            # Salva o arquivo consolidado
            consolidated_filename = "market_data_consolidated_for_ai.json"
            consolidated_path = os.path.join(self.json_folder, consolidated_filename)
            
            with open(consolidated_path, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"[AI] JSON para IA gerado: {consolidated_filename} ({len(json_files)} snapshots)")
            return consolidated_path
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erro ao gerar JSON consolidado: {str(e)}")
            return None
    
    def test_email_config(self):
        """Testa configuração de email"""
        self.logger.info("Testando configuração de email...")
        
        if self.email_sender.test_connection():
            self.logger.info("[OK] Configuração de email OK")
            return True
        else:
            self.logger.error("[ERROR] Problema na configuração de email")
            return False
    
    def run_scheduler(self):
        """Executa o agendador"""
        self.logger.info("=== Market Email Scheduler Iniciado ===")
        
        # Testa configuração de email
        if not self.test_email_config():
            self.logger.error("Parando execução devido a problemas de email")
            return
        
        # Agenda execução a cada 2 minutos
        schedule.every(2).minutes.do(self.collect_and_send_email)
        
        # Executa uma vez imediatamente
        self.logger.info("Executando primeira coleta...")
        self.collect_and_send_email()
        
        self.logger.info("[SCHEDULE] Agendamento ativo: emails a cada 2 minutos")
        self.logger.info("Pressione Ctrl+C para parar")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Verifica a cada 30 segundos
                
        except KeyboardInterrupt:
            self.logger.info("\n=== Scheduler interrompido pelo usuário ===")
        except Exception as e:
            self.logger.error(f"Erro no scheduler: {str(e)}")

def main():
    """Função principal"""
    # Verifica se as variáveis de ambiente estão configuradas
    required_vars = ['EMAIL_USER', 'EMAIL_PASSWORD', 'EMAIL_TO']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("[ERROR] Variáveis de ambiente obrigatórias não configuradas:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nConfigure as variáveis no arquivo .env ou diretamente no sistema")
        print("Exemplo de .env:")
        print("EMAIL_USER=seu_email@gmail.com")
        print("EMAIL_PASSWORD=sua_senha_de_app")
        print("EMAIL_TO=destinatario@gmail.com")
        print("EMAIL_ENABLED=true")
        return
    
    # Verifica se email está habilitado
    if os.getenv('EMAIL_ENABLED', 'false').lower() != 'true':
        print("[ERROR] Email não está habilitado. Configure EMAIL_ENABLED=true")
        return
    
    # Inicia o scheduler
    scheduler = MarketEmailScheduler()
    scheduler.run_scheduler()

if __name__ == "__main__":
    main() 