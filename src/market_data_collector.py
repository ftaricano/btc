import json
from datetime import datetime, timezone
import pandas as pd
from typing import Dict, Any
import logging

from .collectors.binance_futures_collector import BinanceFuturesCollector
from .indicators.technical_indicators import TechnicalIndicators
from .config import SYMBOL, TIMEFRAMES, USE_BINANCE_US

class MarketDataCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.collector = BinanceFuturesCollector()
        self.symbol = SYMBOL

    def _create_dataframe(self, klines: list) -> pd.DataFrame:
        """Converte lista de candles em DataFrame"""
        df = pd.DataFrame(klines, columns=['open', 'high', 'low', 'close', 'volume', 'timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df

    def collect_market_data(self) -> Dict[str, Any]:
        """Coleta todos os dados de mercado e retorna JSON formatado"""
        try:
            # Coleta dados básicos
            current_price = self.collector.get_current_price()
            order_book = self.collector.get_order_book()
            volume_stats = self.collector.get_volume_stats()
            funding_data = self.collector.get_funding_rate()
            open_interest = self.collector.get_open_interest()
            
            # Coleta métricas opcionais
            liquidations_data = self.collector.get_liquidations_24h()
            cvd_data = self.collector.get_cvd_data()

            # Coleta candles para diferentes timeframes
            timeframes_data = {}
            for tf, interval in TIMEFRAMES.items():
                klines = self.collector.get_klines(interval)
                df = self._create_dataframe(klines)
                
                # Calcula indicadores técnicos
                indicators = TechnicalIndicators(df)
                latest_indicators = indicators.get_latest_values()
                
                timeframes_data[tf] = {
                    'candles': klines,
                    'indicators': latest_indicators
                }

            # Monta o JSON final
            market_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'symbol': self.symbol,
                'current_price': current_price,
                
                'order_book': order_book,
                
                'derivatives': {
                    **open_interest,
                    **funding_data
                },
                
                'stats': volume_stats,
                
                'timeframes': timeframes_data
            }
            
            # Adiciona liquidações apenas se disponível
            if liquidations_data:
                market_data['liquidations'] = liquidations_data
            
            # Adiciona flow apenas se disponível
            if cvd_data['perp_cvd'] is not None:
                market_data['flow'] = cvd_data

            return market_data

        except Exception as e:
            self.logger.error(f"Erro ao coletar dados de mercado: {str(e)}")
            raise

    def save_to_file(self, data: Dict[str, Any], filename: str = 'market_data.json'):
        """Salva os dados em um arquivo JSON"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Dados salvos em {filename}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {str(e)}")
            raise

def main():
    # Configura logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Coleta dados
    collector = MarketDataCollector()
    market_data = collector.collect_market_data()
    
    # Salva em arquivo
    collector.save_to_file(market_data)

if __name__ == '__main__':
    main() 