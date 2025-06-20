import json
from datetime import datetime, timezone, timedelta
import pandas as pd
from typing import Dict, Any, List
import logging
import numpy as np

from .collectors.binance_futures_collector import BinanceFuturesCollector
from .indicators.technical_indicators import TechnicalIndicators
from .config import SYMBOL, TIMEFRAMES, USE_BINANCE_US

class MarketDataCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.collector = BinanceFuturesCollector()
        self.symbol = SYMBOL
        # Cache para armazenar histórico de funding e delta volume
        self.funding_history = []
        self.delta_volume_cumulative = []

    def _create_dataframe(self, klines: list) -> pd.DataFrame:
        """Converte lista de candles em DataFrame"""
        df = pd.DataFrame(klines, columns=['open', 'high', 'low', 'close', 'volume', 'timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df

    def _calculate_vwap(self, df: pd.DataFrame, periods: int = None) -> float:
        """Calcula VWAP para um período específico"""
        if periods and len(df) > periods:
            df = df.tail(periods)
        
        # VWAP = (∑(price × volume)) / ∑volume
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).sum() / df['volume'].sum()
        return float(vwap)

    def _calculate_volume_profile(self, df: pd.DataFrame, bins: int = 50) -> Dict:
        """Calcula perfil de volume para determinar POC, VAH, VAL"""
        if len(df) < 2:
            return {"poc": 0, "vah": 0, "val": 0}
        
        # Cria faixas de preço
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_bins = np.linspace(price_min, price_max, bins)
        
        # Distribui volume por faixa de preço
        volume_profile = {}
        for i, row in df.iterrows():
            # Distribui o volume da vela proporcionalmente entre high e low
            candle_range = row['high'] - row['low']
            if candle_range > 0:
                for bin_idx in range(len(price_bins) - 1):
                    bin_low = price_bins[bin_idx]
                    bin_high = price_bins[bin_idx + 1]
                    bin_mid = (bin_low + bin_high) / 2
                    
                    # Verifica se o bin intersecta com a vela
                    if bin_low <= row['high'] and bin_high >= row['low']:
                        # Calcula sobreposição
                        overlap_low = max(bin_low, row['low'])
                        overlap_high = min(bin_high, row['high'])
                        overlap_ratio = (overlap_high - overlap_low) / candle_range
                        
                        if bin_mid not in volume_profile:
                            volume_profile[bin_mid] = 0
                        volume_profile[bin_mid] += row['volume'] * overlap_ratio
        
        if not volume_profile:
            return {"poc": 0, "vah": 0, "val": 0}
        
        # Encontra POC (Point of Control) - preço com maior volume
        poc_price = max(volume_profile, key=volume_profile.get)
        
        # Calcula Value Area (70% do volume)
        total_volume = sum(volume_profile.values())
        target_volume = total_volume * 0.7
        
        # Ordena por volume para encontrar value area
        sorted_prices = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
        
        value_area_volume = 0
        value_area_prices = []
        
        for price, volume in sorted_prices:
            value_area_volume += volume
            value_area_prices.append(price)
            if value_area_volume >= target_volume:
                break
        
        vah = max(value_area_prices) if value_area_prices else poc_price
        val = min(value_area_prices) if value_area_prices else poc_price
        
        return {
            "poc": float(poc_price),
            "vah": float(vah),
            "val": float(val)
        }

    def _detect_absorption(self, candle: List, cvd_change: float) -> bool:
        """Detecta absorção em uma vela"""
        try:
            open_price, high, low, close, volume = candle[:5]
            
            # Critérios para absorção:
            # 1. Alto volume (acima da média)
            # 2. CVD contrário à direção do candle
            # 3. Pavio >= 50% da vela
            
            body_size = abs(close - open_price)
            candle_range = high - low
            
            # Verifica se tem pavio significativo
            if candle_range > 0:
                if close > open_price:  # Candle verde
                    upper_wick = high - close
                    lower_wick = open_price - low
                    max_wick = max(upper_wick, lower_wick)
                    wick_ratio = max_wick / candle_range
                    
                    # Absorção em candle verde: CVD negativo + pavio >= 50%
                    if cvd_change < 0 and wick_ratio >= 0.5:
                        return True
                        
                else:  # Candle vermelho
                    upper_wick = high - open_price
                    lower_wick = close - low
                    max_wick = max(upper_wick, lower_wick)
                    wick_ratio = max_wick / candle_range
                    
                    # Absorção em candle vermelho: CVD positivo + pavio >= 50%
                    if cvd_change > 0 and wick_ratio >= 0.5:
                        return True
            
            return False
            
        except:
            return False

    def _calculate_imbalance_score(self, order_book: Dict, current_price: float) -> float:
        """Calcula score de imbalance baseado na posição do preço no spread"""
        try:
            bids = order_book['top']['bids']
            asks = order_book['top']['asks']
            
            if not bids or not asks:
                return 0.0
            
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            spread = best_ask - best_bid
            
            if spread <= 0:
                return 0.0
            
            # Score varia de -1 (preço colado no bid) a +1 (preço colado no ask)
            # 0 = preço no meio do spread
            mid_price = (best_bid + best_ask) / 2
            position_in_spread = (current_price - mid_price) / (spread / 2)
            
            # Limita entre -1 e 1
            return max(-1.0, min(1.0, position_in_spread))
            
        except:
            return 0.0

    def _update_funding_history(self, current_funding: float):
        """Atualiza histórico de funding rate (mantém últimos 3)"""
        self.funding_history.append(current_funding)
        if len(self.funding_history) > 3:
            self.funding_history = self.funding_history[-3:]

    def _update_delta_volume_cumulative(self, delta_absolute: float):
        """Atualiza delta volume cumulativo"""
        self.delta_volume_cumulative.append(delta_absolute)
        # Mantém apenas os últimos 50 valores para performance
        if len(self.delta_volume_cumulative) > 50:
            self.delta_volume_cumulative = self.delta_volume_cumulative[-50:]

    def collect_market_data(self) -> Dict[str, Any]:
        """Coleta todos os dados de mercado e retorna JSON formatado"""
        try:
            # Coleta dados básicos
            current_price = self.collector.get_current_price()
            order_book = self.collector.get_order_book()
            volume_stats = self.collector.get_volume_stats()
            funding_data = self.collector.get_funding_rate()
            open_interest = self.collector.get_open_interest()
            
            # Atualiza histórico de funding
            self._update_funding_history(funding_data['funding_rate'])
            
            # Calcula delta volume e atualiza histórico
            taker_buy = volume_stats.get('taker_buy_vol_24h', 0)
            taker_sell = volume_stats.get('taker_sell_vol_24h', 0)
            delta_volume_absolute = taker_buy - taker_sell
            self._update_delta_volume_cumulative(delta_volume_absolute)
            
            # Calcula imbalance score
            imbalance_score = self._calculate_imbalance_score(order_book, current_price)
            
            # Coleta métricas opcionais
            liquidations_data = self.collector.get_liquidations_24h()
            cvd_data = self.collector.get_cvd_data()

            # Coleta candles para diferentes timeframes
            timeframes_data = {}
            vwap_data = {}
            
            for tf, interval in TIMEFRAMES.items():
                klines = self.collector.get_klines(interval, limit=200)  # Mais dados para VWAP
                df = self._create_dataframe(klines)
                
                # Calcula VWAP para diferentes períodos
                if tf == '1h':
                    vwap_data['1h'] = self._calculate_vwap(df, 60)  # 60 períodos de 1h
                elif tf == '4h':
                    vwap_data['4h'] = self._calculate_vwap(df, 24)  # 24 períodos de 4h = 4 dias
                elif tf == '1d':
                    # VWAP diário desde abertura UTC (usa dados de hoje apenas)
                    # Para simplificar, usa todos os dados disponíveis se for timeframe diário
                    if len(df) > 0:
                        vwap_data['d'] = self._calculate_vwap(df)
                    else:
                        vwap_data['d'] = current_price
                
                # Calcula volume profile para 4h
                volume_profile_4h = {}
                if tf == '4h':
                    volume_profile_4h = self._calculate_volume_profile(df.tail(24))  # Últimas 4h
                
                # Calcula indicadores técnicos
                indicators = TechnicalIndicators(df)
                latest_indicators = indicators.get_latest_values()
                
                # Adiciona indicadores melhorados para 1h
                if tf == '1h':
                    # Adiciona mais indicadores para análise
                    latest_indicators['advanced'] = {
                        'rsi_14': latest_indicators.get('rsi', {}).get('rsi_14'),
                        'macd': {
                            'line': latest_indicators.get('macd', {}).get('macd'),
                            'signal': latest_indicators.get('macd', {}).get('macd_signal'),
                            'histogram': latest_indicators.get('macd', {}).get('macd_hist')
                        },
                        'ema_9': latest_indicators.get('ema', {}).get('ema_9'),
                        'ema_21': latest_indicators.get('ema', {}).get('ema_21')
                    }
                
                # Detecta absorção nas velas (apenas para 15m)
                enhanced_candles = []
                if tf == '15m':
                    cvd_changes = cvd_data.get('perp_cvd_changes', [0] * len(klines))
                    for i, candle in enumerate(klines):
                        cvd_change = cvd_changes[i] if i < len(cvd_changes) else 0
                        candle_dict = {
                            'ohlcv': candle,
                            'absorcao': self._detect_absorption(candle, cvd_change)
                        }
                        enhanced_candles.append(candle_dict)
                    
                    timeframes_data[tf] = {
                        'candles': enhanced_candles,
                        'indicators': latest_indicators
                    }
                else:
                    timeframes_data[tf] = {
                        'candles': klines,
                        'indicators': latest_indicators
                    }
                
                # Adiciona volume profile para 4h
                if tf == '4h':
                    timeframes_data[tf]['volume_profile_4h'] = volume_profile_4h

            # Monta o JSON final com melhorias
            market_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'symbol': self.symbol,
                'current_price': current_price,
                
                # VWAP implementado
                'vwap': vwap_data,
                
                # Order book com imbalance score
                'order_book': {
                    **order_book,
                    'imbalance_score': imbalance_score
                },
                
                # Derivatives com funding history
                'derivatives': {
                    **open_interest,
                    **funding_data,
                    'funding_history': self.funding_history.copy()
                },
                
                # Stats com delta volume
                'stats': volume_stats,
                
                # Flow com delta volume absoluto e cumulativo
                'flow': {
                    **cvd_data,
                    'delta_volume_absolute': delta_volume_absolute,
                    'delta_volume_cumulative': self.delta_volume_cumulative.copy()
                },
                
                'timeframes': timeframes_data
            }
            
            # Adiciona liquidações apenas se disponível
            if liquidations_data:
                market_data['liquidations'] = liquidations_data
                
                # Tenta calcular clusters de liquidação (simplificado)
                try:
                    long_liq = liquidations_data.get('long_liq_24h', 0)
                    short_liq = liquidations_data.get('short_liq_24h', 0)
                    
                    # Estimativa simples de clusters baseada no preço atual
                    price_ranges = []
                    if long_liq > 0:
                        range_below = f"{int(current_price * 0.98)}-{int(current_price * 0.99)}"
                        price_ranges.append({"range": range_below, "total_usdt": long_liq})
                    
                    if short_liq > 0:
                        range_above = f"{int(current_price * 1.01)}-{int(current_price * 1.02)}"
                        price_ranges.append({"range": range_above, "total_usdt": short_liq})
                    
                    if price_ranges:
                        market_data['liquidations']['liquidations_clusters'] = price_ranges
                except:
                    pass

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