# Coletor de Dados de Mercado - Binance Futures

Este projeto implementa um coletor de dados de mercado para a Binance Futures, fornecendo uma ampla gama de métricas e indicadores técnicos.

## 🚀 Funcionalidades

- Coleta de dados em tempo real da Binance Futures
- **🔥 Liquidações em tempo real via WebSocket** (sem necessidade de API key)
- Suporte a fallback para Binance.US quando necessário
- Cálculo de indicadores técnicos (SMA, EMA, RSI, MACD, Bollinger Bands, ATR)
- Análise de profundidade do order book expandida (até ±2%)
- Métricas de derivativos (Open Interest, Funding Rate)
- CVD (Cumulative Volume Delta) para Perpetual e Spot
- Estatísticas de volume
- Suporte a múltiplos timeframes (15m, 1h, 4h, 1d)

## 📋 Pré-requisitos

- Python 3.10+
- TA-Lib (biblioteca C)
- Dependências Python listadas em `requirements.txt`

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITÓRIO]
cd [NOME_DO_DIRETÓRIO]
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (opcional):
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais (apenas se necessário)
```

## ⚙️ Configuração

O arquivo `.env` é opcional. Só é necessário se você quiser usar funcionalidades que requerem API key:

```env
BINANCE_API_KEY=sua_api_key
BINANCE_SECRET=sua_api_secret
USE_BINANCE_US=False  # True para usar Binance.US como fallback
```

## 🎯 Uso

### Coleta de Dados Completa

```python
from src.market_data_collector import MarketDataCollector

# Inicializa o coletor
collector = MarketDataCollector()

# Coleta dados (inclui WebSocket de liquidações automaticamente)
market_data = collector.collect_market_data()

# Salva em arquivo
collector.save_to_file(market_data, 'market_data.json')
```

### Teste do WebSocket de Liquidações

```bash
python test_websocket.py
```

### Executando o Coletor Principal

```bash
python run_collector.py
```

### Executando os Testes

```bash
pytest tests/
```

## 📊 Estrutura do JSON de Saída

```json
{
  "timestamp": "2024-03-16T03:15:22Z",
  "symbol": "BTCUSDT",
  "current_price": 105448.66,
  
  "order_book": {
    "top": {
      "bids": [[price, qty], ...],
      "asks": [[price, qty], ...]
    },
    "depth_pct": {
      "bids": {"0.5": 8.4, "1": 14.2, "2": 27.8},
      "asks": {"0.5": 10.1, "1": 16.5, "2": 33.0}
    },
    "imbalance_pct": 15.2
  },
  
  "derivatives": {
    "open_interest_usd": 2.65e10,
    "open_interest_coin": 251000,
    "oi_change_4h_pct": -2.3,
    "funding_rate": 0.00012,
    "funding_next": "2024-03-16T04:00:00Z"
  },
  
  "stats": {
    "volume_24h": 6.28e10,
    "taker_buy_vol_24h": 3.11e10,
    "taker_sell_vol_24h": 3.17e10
  },
  
  "liquidations": {
    "long_liqs_24h": 1500000,
    "short_liqs_24h": 2300000,
    "total_liqs_24h": 3800000
  },
  
  "flow": {
    "perp_cvd": -500000,
    "spot_cvd": 200000,
    "perp_buy_volume_sample": 1000000,
    "perp_sell_volume_sample": 1500000,
    "spot_buy_volume_sample": 800000,
    "spot_sell_volume_sample": 600000
  },
  
  "timeframes": {
    "15m": {
      "candles": [[open, high, low, close, volume, timestamp], ...],
      "indicators": {
        "sma": {"sma_20": 105000, "sma_50": 104500, "sma_200": null},
        "ema": {"ema_9": 105100, "ema_21": 104800, "ema_50": 104600},
        "rsi": {"rsi_14": 65.5},
        "macd": {"macd": 150.2, "macd_signal": 120.1, "macd_hist": 30.1},
        "bollinger": {"bb_upper": 106000, "bb_middle": 105000, "bb_lower": 104000, "bb_width": 0.019},
        "atr": {"atr": 250.5}
      }
    },
    "1h": {...},
    "4h": {...},
    "1d": {...}
  }
}
```

## 🔄 Rate Limiting

O sistema implementa um mecanismo de retry exponencial para lidar com rate limits da API:

- Backoff inicial: 1 segundo
- Backoff máximo: 32 segundos
- Máximo de tentativas: 3

## 🌐 WebSocket de Liquidações

### Vantagens:
- **📡 Tempo real**: Liquidações processadas instantaneamente
- **🆓 Gratuito**: Não requer API key
- **🔄 Auto-reconexão**: Reconecta automaticamente se desconectar
- **📊 Precisão**: Dados mais precisos que polling da API REST

### Como funciona:
1. Conecta ao WebSocket público: `wss://fstream.binance.com/ws/!forceOrder@arr`
2. Filtra liquidações do símbolo BTCUSDT
3. Acumula valores por 24h (reseta automaticamente)
4. Fallback para API REST se WebSocket falhar

## 📝 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📧 Contato

Seu Nome - [@seu_twitter](https://twitter.com/seu_twitter) - email@exemplo.com

Link do Projeto: [https://github.com/seu-usuario/btc-analysis](https://github.com/seu-usuario/btc-analysis) 