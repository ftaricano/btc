import os
import time
import json
from datetime import datetime
import pandas as pd
import numpy as np
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
import ta
from dotenv import load_dotenv

class BTCAnalyzer:
    def __init__(self):
        # Inicializa o cliente Binance (sem chaves de API para dados públicos)
        self.client = Client()
        self.symbol = "BTCUSDT"
        self.timeframes = {
            "1h": Client.KLINE_INTERVAL_1HOUR,
            "4h": Client.KLINE_INTERVAL_4HOUR,
            "1d": Client.KLINE_INTERVAL_1DAY
        }
        
    def get_current_price(self):
        """Obtém o preço atual do BTC/USDT"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            print(f"Erro ao obter preço atual: {e}")
            return None

    def get_klines(self, timeframe, limit=100):
        """Obtém os candles para um timeframe específico"""
        try:
            klines = self.client.get_klines(
                symbol=self.symbol,
                interval=self.timeframes[timeframe],
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Converter tipos de dados
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'taker_buy_base', 'taker_buy_quote']:
                df[col] = df[col].astype(float)
                
            return df
        except BinanceAPIException as e:
            print(f"Erro ao obter candles: {e}")
            return None

    def get_order_book(self, limit=10):
        """Obtém o livro de ordens"""
        try:
            depth = self.client.get_order_book(symbol=self.symbol, limit=limit)
            return {
                'bids': depth['bids'][:limit],
                'asks': depth['asks'][:limit]
            }
        except BinanceAPIException as e:
            print(f"Erro ao obter livro de ordens: {e}")
            return None

    def calculate_volume_indicators(self, df):
        """Calcula indicadores de volume"""
        # Volume médio
        df['volume_sma_20'] = ta.volume.volume_weighted_average_price(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            volume=df['volume'],
            window=20
        )
        
        # OBV (On Balance Volume)
        df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
        
        # Volume ROC (Rate of Change) - calculado manualmente
        df['volume_roc'] = df['volume'].pct_change(periods=14) * 100
        
        # MFI (Money Flow Index)
        df['mfi'] = ta.volume.money_flow_index(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            volume=df['volume'],
            window=14
        )
        
        # Chaikin Money Flow
        df['cmf'] = ta.volume.chaikin_money_flow(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            volume=df['volume'],
            window=20
        )
        
        # Ease of Movement
        df['eom'] = ta.volume.ease_of_movement(
            high=df['high'],
            low=df['low'],
            volume=df['volume'],
            window=14
        )
        
        # Volume Force Index
        df['vfi'] = ta.volume.force_index(
            close=df['close'],
            volume=df['volume'],
            window=13
        )
        
        return df

    def calculate_indicators(self, df):
        """Calcula os indicadores técnicos"""
        # Médias Móveis
        df['SMA_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
        df['EMA_9'] = ta.trend.ema_indicator(df['close'], window=9)
        df['EMA_21'] = ta.trend.ema_indicator(df['close'], window=21)
        df['EMA_50'] = ta.trend.ema_indicator(df['close'], window=50)
        df['EMA_200'] = ta.trend.ema_indicator(df['close'], window=200)
        
        # RSI
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        df['RSI_21'] = ta.momentum.rsi(df['close'], window=21)
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['BB_Upper'] = bollinger.bollinger_hband()
        df['BB_Lower'] = bollinger.bollinger_lband()
        df['BB_Middle'] = bollinger.bollinger_mavg()
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle'].replace(0, np.nan)
        
        # Stochastic
        stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()
        
        # ADX (Average Directional Index)
        adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
        df['ADX'] = adx.adx()
        df['ADX_Pos'] = adx.adx_pos()
        df['ADX_Neg'] = adx.adx_neg()
        
        # ATR (Average True Range)
        df['ATR'] = ta.volatility.average_true_range(
            df['high'],
            df['low'],
            df['close'],
            window=14
        )
        
        # Momentum
        df['ROC'] = ta.momentum.roc(df['close'], window=10)
        
        # Volume Indicators
        df = self.calculate_volume_indicators(df)
        
        return df

    def analyze_trend(self, df):
        """Analisa a tendência baseada nos indicadores"""
        last_row = df.iloc[-1]
        
        trend_signals = {
            'price_above_sma200': last_row['close'] > last_row['SMA_200'],
            'price_above_sma50': last_row['close'] > last_row['SMA_50'],
            'sma50_above_sma200': last_row['SMA_50'] > last_row['SMA_200'],
            'rsi_bullish': last_row['RSI'] > 50,
            'macd_bullish': last_row['MACD'] > last_row['MACD_Signal'],
            'price_above_bb_middle': last_row['close'] > last_row['BB_Middle'],
            'stoch_bullish': last_row['Stoch_K'] > last_row['Stoch_D'],
            'adx_strong_trend': last_row['ADX'] > 25,
            'cmf_positive': last_row['cmf'] > 0,
            'mfi_bullish': last_row['mfi'] > 50
        }
        
        bullish_signals = sum(trend_signals.values())
        
        if bullish_signals >= 7:
            return "ALTA"
        elif bullish_signals <= 3:
            return "BAIXA"
        else:
            return "LATERAL"

    def find_support_resistance(self, df, window=20):
        """Encontra níveis de suporte e resistência"""
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        current_price = df['close'].iloc[-1]
        
        # Encontra os níveis mais próximos do preço atual
        supports = lows[lows < current_price].tail(3).tolist()
        resistances = highs[highs > current_price].head(3).tolist()
        
        return {
            'supports': supports,
            'resistances': resistances
        }

    def get_trading_suggestion(self, df, trend):
        """Gera sugestão de trade baseada na análise"""
        current_price = df['close'].iloc[-1]
        sr_levels = self.find_support_resistance(df)
        
        if trend == "ALTA":
            entry = current_price
            stop = min(sr_levels['supports']) if sr_levels['supports'] else current_price * 0.98
            target = max(sr_levels['resistances']) if sr_levels['resistances'] else current_price * 1.03
        elif trend == "BAIXA":
            entry = current_price
            stop = max(sr_levels['resistances']) if sr_levels['resistances'] else current_price * 1.02
            target = min(sr_levels['supports']) if sr_levels['supports'] else current_price * 0.97
        else:
            return None
            
        return {
            'entry': entry,
            'stop': stop,
            'target': target,
            'risk_reward': abs(target - entry) / abs(stop - entry)
        }

    def get_market_metrics(self, df):
        """Obtém métricas adicionais do mercado"""
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        return {
            'price_change_24h': ((last_row['close'] - df.iloc[-24]['close']) / df.iloc[-24]['close']) * 100 if len(df) >= 24 else None,
            'volume_change_24h': ((last_row['volume'] - df.iloc[-24]['volume']) / df.iloc[-24]['volume']) * 100 if len(df) >= 24 else None,
            'volatility': last_row['ATR'] / last_row['close'] * 100,
            'volume_profile': {
                'current_volume': last_row['volume'],
                'volume_sma_20': last_row['volume_sma_20'],
                'volume_ratio': last_row['volume'] / last_row['volume_sma_20'] if last_row['volume_sma_20'] != 0 else None
            },
            'momentum': {
                'rsi': last_row['RSI'],
                'stoch_k': last_row['Stoch_K'],
                'stoch_d': last_row['Stoch_D'],
                'macd': last_row['MACD'],
                'macd_signal': last_row['MACD_Signal'],
                'macd_hist': last_row['MACD_Hist']
            },
            'trend_strength': {
                'adx': last_row['ADX'],
                'adx_positive': last_row['ADX_Pos'],
                'adx_negative': last_row['ADX_Neg']
            },
            'volatility_indicators': {
                'bb_width': last_row['BB_Width'],
                'atr': last_row['ATR'],
                'atr_percent': (last_row['ATR'] / last_row['close']) * 100
            }
        }

    def convert_to_serializable(self, obj):
        """Converte objetos para tipos serializáveis"""
        if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self.convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self.convert_to_serializable(item) for item in obj)
        elif pd.isna(obj):
            return None
        return obj

    def run_analysis(self):
        """Executa a análise completa e retorna um JSON detalhado"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'symbol': self.symbol,
            'current_price': self.get_current_price(),
            'order_book': self.get_order_book(),
            'timeframes': {}
        }
        
        for timeframe in self.timeframes:
            df = self.get_klines(timeframe)
            if df is not None:
                df = self.calculate_indicators(df)
                trend = self.analyze_trend(df)
                
                timeframe_data = {
                    'trend': trend,
                    'support_resistance': self.find_support_resistance(df),
                    'trading_suggestion': self.get_trading_suggestion(df, trend),
                    'market_metrics': self.get_market_metrics(df),
                    'indicators': {
                        'moving_averages': {
                            'sma_20': float(df['SMA_20'].iloc[-1]),
                            'sma_50': float(df['SMA_50'].iloc[-1]),
                            'sma_200': float(df['SMA_200'].iloc[-1]),
                            'ema_9': float(df['EMA_9'].iloc[-1]),
                            'ema_21': float(df['EMA_21'].iloc[-1]),
                            'ema_50': float(df['EMA_50'].iloc[-1]),
                            'ema_200': float(df['EMA_200'].iloc[-1])
                        },
                        'momentum': {
                            'rsi': float(df['RSI'].iloc[-1]),
                            'rsi_21': float(df['RSI_21'].iloc[-1]),
                            'stoch_k': float(df['Stoch_K'].iloc[-1]),
                            'stoch_d': float(df['Stoch_D'].iloc[-1])
                        },
                        'trend': {
                            'macd': float(df['MACD'].iloc[-1]),
                            'macd_signal': float(df['MACD_Signal'].iloc[-1]),
                            'macd_hist': float(df['MACD_Hist'].iloc[-1]),
                            'adx': float(df['ADX'].iloc[-1])
                        },
                        'volatility': {
                            'bb_upper': float(df['BB_Upper'].iloc[-1]),
                            'bb_middle': float(df['BB_Middle'].iloc[-1]),
                            'bb_lower': float(df['BB_Lower'].iloc[-1]),
                            'bb_width': float(df['BB_Width'].iloc[-1]),
                            'atr': float(df['ATR'].iloc[-1])
                        },
                        'volume': {
                            'obv': float(df['obv'].iloc[-1]),
                            'volume_roc': float(df['volume_roc'].iloc[-1]),
                            'mfi': float(df['mfi'].iloc[-1]),
                            'cmf': float(df['cmf'].iloc[-1]),
                            'eom': float(df['eom'].iloc[-1]),
                            'vfi': float(df['vfi'].iloc[-1])
                        }
                    },
                    'candles': {
                        'last_5': df.tail(5)[['timestamp', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
                    }
                }
                
                # Converte todos os valores para tipos serializáveis
                results['timeframes'][timeframe] = self.convert_to_serializable(timeframe_data)
        
        return self.convert_to_serializable(results)

def main():
    analyzer = BTCAnalyzer()
    results = analyzer.run_analysis()
    
    # Salva o JSON em um arquivo
    with open('btc_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nAnálise completa salva em 'btc_analysis.json'")
    print(f"Preço Atual: ${results['current_price']:.2f}")
    
    # Exibe um resumo dos resultados
    for timeframe, data in results['timeframes'].items():
        print(f"\nTimeframe {timeframe}:")
        print(f"Tendência: {data['trend']}")
        if data['trading_suggestion']:
            print("Sugestão de Trade:")
            print(f"Entrada: ${data['trading_suggestion']['entry']:.2f}")
            print(f"Stop: ${data['trading_suggestion']['stop']:.2f}")
            print(f"Alvo: ${data['trading_suggestion']['target']:.2f}")
            print(f"Risco/Retorno: {data['trading_suggestion']['risk_reward']:.2f}")

if __name__ == "__main__":
    main() 