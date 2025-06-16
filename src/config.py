import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações da API
USE_BINANCE_US = os.getenv('USE_BINANCE_US', 'False').lower() == 'true'
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET = os.getenv('BINANCE_SECRET')

# URLs da API
BINANCE_FUTURES_URL = 'https://fapi.binance.com'
BINANCE_US_URL = 'https://api.binance.us'
COINGLASS_URL = 'https://open-api.coinglass.com'

# Configurações do coletor
SYMBOL = 'BTCUSDT'
TIMEFRAMES = {
    '15m': '15m',
    '1h': '1h',
    '4h': '4h',
    '1d': '1d'
}

# Configurações de rate limit
MAX_RETRIES = 3
INITIAL_BACKOFF = 1
MAX_BACKOFF = 32

# Configurações de indicadores
INDICATOR_PARAMS = {
    'SMA': [20, 50, 200],
    'EMA': [9, 21, 50],
    'RSI': [14],
    'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
    'BB': {'window': 20, 'std': 2},
    'ATR': {'window': 14}
}

# Configurações de depth
DEPTH_LEVELS = [0.5, 1.0, 2.0]  # Percentuais para cálculo de profundidade
ORDER_BOOK_LIMIT = 20  # Número de níveis no top do book 