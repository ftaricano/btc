# Análise Técnica BTC/USDT

Este projeto realiza uma análise técnica completa do par BTC/USDT usando a API pública da Binance, com uma interface web interativa construída em Streamlit.

## 🚀 Funcionalidades

- Coleta de preço atual em tempo real
- Análise de candles em múltiplos timeframes (1h, 4h, 1d)
- Cálculo de indicadores técnicos:
  - Médias Móveis (SMA 20, 50, 200 / EMA 9, 21, 50, 200)
  - RSI (14, 21)
  - MACD (12, 26, 9)
  - Bandas de Bollinger
  - Stochastic
  - ADX
  - ATR
  - Indicadores de Volume (OBV, MFI, CMF, EOM, VFI)
- Análise de tendência
- Identificação de suportes e resistências
- Sugestões de trade com entrada, stop e alvo
- Interface web interativa
- Exportação de dados em JSON

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/btc-analysis.git
cd btc-analysis
```

2. Crie um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🎮 Uso

### Interface Web (Recomendado)

1. Execute o Streamlit:
```bash
streamlit run app.py
```

2. Acesse a interface web no navegador (geralmente em http://localhost:8501)

3. Use o botão "Atualizar Análise" para obter dados em tempo real

### Script Python

1. Execute o script principal:
```bash
python btc_analysis.py
```

2. O script irá gerar um arquivo `btc_analysis.json` com todos os dados

## 📊 Saída

O projeto gera:

- Interface web interativa com:
  - Gráficos de candlestick
  - Tabelas de indicadores
  - Métricas em tempo real
  - JSON exportável
- Arquivo JSON com:
  - Preço atual
  - Análise por timeframe
  - Indicadores técnicos
  - Suportes e resistências
  - Sugestões de trade

## 🛠️ Tecnologias Utilizadas

- Python
- Streamlit
- Pandas
- NumPy
- TA-Lib
- Plotly
- Binance API

## 📝 Notas

- Este projeto usa apenas a API pública da Binance
- Os indicadores técnicos são calculados localmente
- As sugestões de trade são baseadas em análise técnica
- Sempre faça sua própria análise e use gerenciamento de risco adequado

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📧 Contato

Seu Nome - [@seu_twitter](https://twitter.com/seu_twitter) - email@exemplo.com

Link do Projeto: [https://github.com/seu-usuario/btc-analysis](https://github.com/seu-usuario/btc-analysis) 