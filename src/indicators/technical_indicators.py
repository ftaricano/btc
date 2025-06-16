import pandas as pd
import numpy as np
import ta
from typing import Dict, List
from ..config import INDICATOR_PARAMS

class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.close = df['close']
        self.high = df['high']
        self.low = df['low']
        self.volume = df['volume']
        self.open = df['open']

    def calculate_all(self) -> Dict:
        """Calcula todos os indicadores técnicos"""
        return {
            'sma': self.calculate_sma(),
            'ema': self.calculate_ema(),
            'rsi': self.calculate_rsi(),
            'macd': self.calculate_macd(),
            'bollinger': self.calculate_bollinger(),
            'atr': self.calculate_atr()
        }

    def calculate_sma(self) -> Dict[str, pd.Series]:
        """Calcula SMAs para diferentes períodos"""
        return {
            f'sma_{period}': ta.trend.sma_indicator(self.close, window=period)
            for period in INDICATOR_PARAMS['SMA']
        }

    def calculate_ema(self) -> Dict[str, pd.Series]:
        """Calcula EMAs para diferentes períodos"""
        return {
            f'ema_{period}': ta.trend.ema_indicator(self.close, window=period)
            for period in INDICATOR_PARAMS['EMA']
        }

    def calculate_rsi(self) -> Dict[str, pd.Series]:
        """Calcula RSI"""
        return {
            f'rsi_{period}': ta.momentum.rsi(self.close, window=period)
            for period in INDICATOR_PARAMS['RSI']
        }

    def calculate_macd(self) -> Dict[str, pd.Series]:
        """Calcula MACD"""
        params = INDICATOR_PARAMS['MACD']
        macd = ta.trend.MACD(
            self.close,
            window_fast=params['fast'],
            window_slow=params['slow'],
            window_sign=params['signal']
        )
        
        return {
            'macd': macd.macd(),
            'macd_signal': macd.macd_signal(),
            'macd_hist': macd.macd_diff()
        }

    def calculate_bollinger(self) -> Dict[str, pd.Series]:
        """Calcula Bollinger Bands"""
        params = INDICATOR_PARAMS['BB']
        bollinger = ta.volatility.BollingerBands(
            self.close,
            window=params['window'],
            window_dev=params['std']
        )
        
        return {
            'bb_upper': bollinger.bollinger_hband(),
            'bb_middle': bollinger.bollinger_mavg(),
            'bb_lower': bollinger.bollinger_lband(),
            'bb_width': (bollinger.bollinger_hband() - bollinger.bollinger_lband()) / bollinger.bollinger_mavg()
        }

    def calculate_atr(self) -> Dict[str, pd.Series]:
        """Calcula ATR"""
        params = INDICATOR_PARAMS['ATR']
        return {
            'atr': ta.volatility.average_true_range(
                self.high,
                self.low,
                self.close,
                window=params['window']
            )
        }

    def get_latest_values(self) -> Dict:
        """Retorna os valores mais recentes de todos os indicadores"""
        indicators = self.calculate_all()
        latest = {}
        
        # Verifica quantos dados temos disponíveis
        data_length = len(self.df)
        
        # Lista de indicadores que devem sempre estar presentes (mesmo que null)
        required_indicators = {
            'sma': ['sma_20', 'sma_50'],
            'ema': ['ema_9', 'ema_21', 'ema_50'],
            'rsi': ['rsi_14'],
            'macd': ['macd', 'macd_signal', 'macd_hist'],
            'bollinger': ['bb_upper', 'bb_middle', 'bb_lower', 'bb_width'],
            'atr': ['atr']
        }
        
        # Adiciona SMA/EMA 200 apenas se temos dados suficientes (pelo menos 200 períodos)
        if data_length >= 200:
            required_indicators['sma'].append('sma_200')
            # EMA 50 é suficiente, não precisamos de EMA 200 para timeframes curtos
        
        for category, values in indicators.items():
            latest[category] = {}
            
            # Primeiro, adiciona todos os valores calculados
            for name, series in values.items():
                # Só inclui se está na lista de obrigatórios ou se temos dados suficientes
                if category in required_indicators and name in required_indicators[category]:
                    value = series.iloc[-1]
                    if pd.notna(value):
                        latest[category][name] = float(value)
                    else:
                        latest[category][name] = None
                elif name not in ['sma_200']:  # Inclui outros indicadores normalmente
                    value = series.iloc[-1]
                    if pd.notna(value):
                        latest[category][name] = float(value)
            
            # Garante que indicadores obrigatórios estejam presentes
            if category in required_indicators:
                for required_name in required_indicators[category]:
                    if required_name not in latest[category]:
                        latest[category][required_name] = None
        
        return latest 