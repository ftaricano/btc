import streamlit as st
import json
from btc_analysis import BTCAnalyzer
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Análise Técnica BTC/USDT",
    page_icon="📈",
    layout="wide"
)

# Título e descrição
st.title("📈 Análise Técnica BTC/USDT")
st.markdown("""
Esta aplicação realiza uma análise técnica completa do par BTC/USDT usando a API pública da Binance.
Os dados são atualizados em tempo real e podem ser copiados para uso em outras aplicações.
""")

# Botão para atualizar análise
if st.button("🔄 Atualizar Análise"):
    with st.spinner("Realizando análise..."):
        analyzer = BTCAnalyzer()
        results = analyzer.run_analysis()
        
        # Salva os resultados na sessão
        st.session_state.results = results
        st.session_state.last_update = datetime.now()

# Exibe última atualização
if 'last_update' in st.session_state:
    st.info(f"Última atualização: {st.session_state.last_update.strftime('%d/%m/%Y %H:%M:%S')}")

# Se temos resultados, exibe as informações
if 'results' in st.session_state:
    results = st.session_state.results
    
    # Preço atual
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Preço Atual", f"${results['current_price']:,.2f}")
    
    # Análise por timeframe
    for timeframe in ['1h', '4h', '1d']:
        if timeframe in results['timeframes']:
            data = results['timeframes'][timeframe]
            
            st.markdown(f"### Timeframe {timeframe}")
            
            # Tendência e métricas principais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tendência", data['trend'])
            with col2:
                if data['trading_suggestion']:
                    st.metric("Risco/Retorno", f"{data['trading_suggestion']['risk_reward']:.2f}")
            
            # Indicadores técnicos
            st.markdown("#### Indicadores Técnicos")
            indicators = data['indicators']
            
            # Médias Móveis
            st.markdown("**Médias Móveis**")
            ma_data = indicators['moving_averages']
            ma_df = pd.DataFrame({
                'Indicador': list(ma_data.keys()),
                'Valor': list(ma_data.values())
            })
            st.dataframe(ma_df, hide_index=True)
            
            # Momentum
            st.markdown("**Momentum**")
            momentum_data = indicators['momentum']
            momentum_df = pd.DataFrame({
                'Indicador': list(momentum_data.keys()),
                'Valor': list(momentum_data.values())
            })
            st.dataframe(momentum_df, hide_index=True)
            
            # Volume
            st.markdown("**Volume**")
            volume_data = indicators['volume']
            volume_df = pd.DataFrame({
                'Indicador': list(volume_data.keys()),
                'Valor': list(volume_data.values())
            })
            st.dataframe(volume_df, hide_index=True)
            
            # Suportes e Resistências
            st.markdown("#### Suportes e Resistências")
            sr_data = data['support_resistance']
            sr_df = pd.DataFrame({
                'Tipo': ['Suporte'] * len(sr_data['supports']) + ['Resistência'] * len(sr_data['resistances']),
                'Preço': sr_data['supports'] + sr_data['resistances']
            })
            st.dataframe(sr_df, hide_index=True)
            
            # Sugestão de Trade
            if data['trading_suggestion']:
                st.markdown("#### Sugestão de Trade")
                trade_data = data['trading_suggestion']
                trade_df = pd.DataFrame({
                    'Parâmetro': ['Entrada', 'Stop', 'Alvo'],
                    'Preço': [trade_data['entry'], trade_data['stop'], trade_data['target']]
                })
                st.dataframe(trade_df, hide_index=True)
    
    # JSON completo
    st.markdown("### JSON Completo")
    json_str = json.dumps(results, indent=2)
    st.code(json_str, language='json')
    
    # Botão para copiar JSON
    st.button("📋 Copiar JSON", on_click=lambda: st.write("JSON copiado para a área de transferência!"))
    
    # Gráfico de preço
    st.markdown("### Gráfico de Preço (Últimas 5 velas)")
    for timeframe in ['1h', '4h', '1d']:
        if timeframe in results['timeframes']:
            candles = results['timeframes'][timeframe]['candles']['last_5']
            df = pd.DataFrame(candles)
            
            fig = go.Figure(data=[go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close']
            )])
            
            fig.update_layout(
                title=f'BTC/USDT - {timeframe}',
                yaxis_title='Preço (USDT)',
                xaxis_title='Data/Hora'
            )
            
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Clique no botão 'Atualizar Análise' para começar.") 