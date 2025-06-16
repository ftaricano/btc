# BTC Market Data Collector

Sistema robusto para coleta de dados de mercado do Bitcoin (BTCUSDT) da Binance Futures em tempo real.

## 🚀 Funcionalidades

### **Dados Coletados:**
- **MARKET**: Preço atual (markPrice)
- **ORDER_BOOK**: Top 20 níveis + profundidade percentual (0.5%, 1%, 2%)
- **CANDLES**: 50 candles para múltiplos timeframes (15m, 1h, 4h, 1d)
- **INDICADORES**: SMA, EMA, RSI, MACD, Bollinger Bands, ATR
- **DERIVATIVOS**: Open Interest, variação OI 4h, funding rate
- **VOLUME**: Volume 24h, taker buy/sell volumes
- **LIQUIDAÇÕES**: WebSocket tempo real de liquidações Long/Short 24h
- **FLOW (CVD)**: Cumulative Volume Delta para Perpetual e Spot

### **Características Técnicas:**
- ✅ WebSocket tempo real para liquidações (~50ms latency)
- ✅ Rate limiting com backoff exponencial
- ✅ Fallbacks inteligentes para APIs
- ✅ Saída JSON padronizada
- ✅ Logs detalhados
- ✅ Tratamento robusto de erros

## 📱 **NOVO: Acesso pelo Celular**

### **Opção 1: Interface Web (Recomendada)**

1. **No computador:**
   ```bash
   # Descobrir IP local
   python get_ip.py
   
   # Iniciar servidor web
   python web_collector.py
   ```

2. **No celular:**
   - Conecte na mesma rede WiFi
   - Acesse: `http://SEU-IP:8080`
   - Clique em "📊 Coletar Dados"
   - Use "📋 Copiar JSON" para copiar os dados

### **Opção 2: Termux (Android)**

1. **Instalar Termux:**
   ```bash
   # No Termux
   pkg update && pkg upgrade
   pkg install python git
   pip install -r requirements.txt
   ```

2. **Executar:**
   ```bash
   python run_collector.py
   cat market_data_*.json | termux-clipboard-set
   ```

## 💻 Instalação (Desktop)

### **Pré-requisitos:**
- Python 3.8+
- pip

### **Instalação:**
```bash
# Clonar repositório
git clone <repositorio>
cd btc

# Instalar dependências
pip install -r requirements.txt

# Executar
python run_collector.py
```

## 🔧 Configuração

### **Variáveis de Ambiente (Opcional):**
```bash
# .env
USE_BINANCE_US=False  # True para Binance.US
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR
```

## 📊 Uso

### **Coleta Simples:**
```bash
python run_collector.py
```

### **Interface Web:**
```bash
python web_collector.py
# Acesse: http://localhost:8080
```

### **Descobrir IP para Celular:**
```bash
python get_ip.py
```

## 📁 Estrutura do Projeto

```
btc/
├── src/
│   ├── collectors/
│   │   ├── base_collector.py           # Classe base
│   │   ├── binance_futures_collector.py # Coletor principal
│   │   └── websocket_liquidations.py   # WebSocket liquidações
│   ├── indicators/
│   │   └── technical_indicators.py     # Indicadores técnicos
│   ├── config.py                       # Configurações
│   └── market_data_collector.py        # Orquestrador
├── tests/
│   └── test_market_data.py            # Testes automatizados
├── run_collector.py                   # Script principal
├── web_collector.py                   # Interface web
├── get_ip.py                         # Descobrir IP local
├── requirements.txt                   # Dependências
└── README.md                         # Documentação
```

## 🔍 Exemplo de Saída JSON

```json
{
  "timestamp": "2025-06-16T01:20:42.903843+00:00",
  "symbol": "BTCUSDT",
  "current_price": 105113.46,
  "order_book": {
    "top": {
      "bids": [[105100.00, 7.057], [105099.90, 0.002]],
      "asks": [[105100.10, 9.263], [105100.20, 0.035]]
    },
    "depth_pct": {
      "bids": {"0.5": 113.59, "1.0": 113.59, "2.0": 113.59},
      "asks": {"0.5": 147.92, "1.0": 147.92, "2.0": 147.92}
    },
    "imbalance_pct": -13.1
  },
  "derivatives": {
    "open_interest_usd": 8250000000,
    "open_interest_btc": 78450,
    "oi_change_4h_pct": -0.79,
    "funding_rate": 0.0005,
    "next_funding_time": "2025-06-16T08:00:00+00:00"
  },
  "stats": {
    "volume_24h": 8460000000,
    "taker_buy_vol_24h": 4230000000,
    "taker_sell_vol_24h": 4230000000
  },
  "liquidations": {
    "long_liqs_24h": 0.0,
    "short_liqs_24h": 0.0,
    "total_liqs_24h": 0.0
  },
  "flow": {
    "perp_cvd": 2210000,
    "spot_cvd": 305940,
    "perp_buy_vol": 3850000,
    "perp_sell_vol": 1640000,
    "spot_buy_vol": 592010,
    "spot_sell_vol": 286080
  },
  "timeframes": {
    "15m": {
      "candles": [...],
      "indicators": {
        "sma_20": 105109.29,
        "sma_50": 105307.86,
        "ema_9": 105269.82,
        "rsi_14": 45.13,
        "macd": {"macd": 20.72, "signal": 13.50, "histogram": 7.22},
        "bollinger": {"upper": 105767.64, "middle": 105109.29, "lower": 104450.94},
        "atr_14": 248.62
      }
    }
  }
}
```

## 🧪 Testes

```bash
# Executar testes
python -m pytest tests/ -v

# Teste específico
python -m pytest tests/test_market_data.py -v
```

## 📈 Monitoramento

### **Logs:**
- Conexão WebSocket em tempo real
- Rate limiting e backoffs
- Fallbacks automáticos
- Métricas de performance

### **Métricas:**
- Latência de coleta
- Taxa de sucesso das APIs
- Uptime do WebSocket
- Volume de dados processados

## 🔧 Troubleshooting

### **WebSocket desconectado:**
- Verifique conexão com internet
- Logs mostrarão tentativas de reconexão

### **Rate limiting:**
- Sistema tem backoff automático
- Aguarde alguns segundos

### **Dados faltando:**
- Campos opcionais são removidos quando indisponíveis
- Verifique logs para detalhes

## 📄 Licença

MIT License - veja LICENSE para detalhes.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

**Desenvolvido com ❤️ para traders e desenvolvedores** 