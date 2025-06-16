from src.market_data_collector import MarketDataCollector
import json
from datetime import datetime

def format_number(num):
    """Formata números grandes de forma legível"""
    if num >= 1e9:
        return f"{num/1e9:.2f}B"
    elif num >= 1e6:
        return f"{num/1e6:.2f}M"
    elif num >= 1e3:
        return f"{num/1e3:.2f}K"
    return f"{num:.2f}"

def print_market_summary(market_data):
    """Imprime um resumo completo dos dados de mercado"""
    print("\n=== RESUMO DO MERCADO ===")
    print(f"Timestamp: {market_data['timestamp']}")
    print(f"Símbolo: {market_data['symbol']}")
    print(f"Preço Atual: {market_data['current_price']:.2f} USDT")
    
    print("\n=== ORDER BOOK ===")
    print("Top 5 Bids:")
    for price, qty in market_data['order_book']['top']['bids'][:5]:
        print(f"  {price:.2f} USDT - {qty:.4f} BTC")
    print("\nTop 5 Asks:")
    for price, qty in market_data['order_book']['top']['asks'][:5]:
        print(f"  {price:.2f} USDT - {qty:.4f} BTC")
    
    print("\nProfundidade do Book:")
    for pct in ['0.5', '1.0', '2.0']:
        print(f"\n{pct}% do preço:")
        print(f"  Bids: {format_number(market_data['order_book']['depth_pct']['bids'][pct])} BTC")
        print(f"  Asks: {format_number(market_data['order_book']['depth_pct']['asks'][pct])} BTC")
    
    # Adiciona imbalance
    imbalance = market_data['order_book']['imbalance_pct']
    if imbalance > 0:
        print(f"\nImbalance: +{imbalance:.1f}% (pressão compradora)")
    elif imbalance < 0:
        print(f"\nImbalance: {imbalance:.1f}% (pressão vendedora)")
    else:
        print(f"\nImbalance: {imbalance:.1f}% (equilibrado)")
    
    print("\n=== DERIVATIVOS ===")
    print(f"Open Interest (USD): {format_number(market_data['derivatives']['open_interest_usd'])} USDT")
    print(f"Open Interest (BTC): {format_number(market_data['derivatives']['open_interest_coin'])} BTC")
    print(f"Variação OI 4h: {market_data['derivatives']['oi_change_4h_pct']:.2f}%")
    print(f"Taxa de Funding: {market_data['derivatives']['funding_rate']*100:.4f}%")
    print(f"Próximo Funding: {market_data['derivatives']['funding_next']}")
    
    print("\n=== VOLUME ===")
    print(f"Volume 24h: {format_number(market_data['stats']['volume_24h'])} USDT")
    print(f"Volume Compra 24h: {format_number(market_data['stats']['taker_buy_vol_24h'])} USDT")
    print(f"Volume Venda 24h: {format_number(market_data['stats']['taker_sell_vol_24h'])} USDT")
    
    print("\n=== INDICADORES TÉCNICOS (15m) ===")
    indicators = market_data['timeframes']['15m']['indicators']
    
    print("\nMédias Móveis:")
    # SMA: 20, 50, 200 (se disponível)
    for period in ['20', '50', '200']:
        sma_key = f'sma_{period}'
        if sma_key in indicators.get('sma', {}):
            value = indicators['sma'][sma_key]
            if value is not None:
                print(f"  SMA {period}: {value:.2f}")
            else:
                print(f"  SMA {period}: null (dados insuficientes)")
    
    # EMA: 9, 21, 50
    for period in ['9', '21', '50']:
        ema_key = f'ema_{period}'
        if ema_key in indicators.get('ema', {}):
            value = indicators['ema'][ema_key]
            if value is not None:
                print(f"  EMA {period}: {value:.2f}")
            else:
                print(f"  EMA {period}: null (dados insuficientes)")
    
    print("\nRSI:")
    if 'rsi_14' in indicators.get('rsi', {}):
        value = indicators['rsi']['rsi_14']
        if value is not None:
            print(f"  RSI 14: {value:.2f}")
        else:
            print("  RSI 14: null")
    
    print("\nMACD:")
    if 'macd' in indicators.get('macd', {}):
        macd_val = indicators['macd'].get('macd')
        signal_val = indicators['macd'].get('macd_signal')
        hist_val = indicators['macd'].get('macd_hist')
        if macd_val is not None:
            print(f"  MACD: {macd_val:.2f}")
            print(f"  Signal: {signal_val:.2f}")
            print(f"  Histograma: {hist_val:.2f}")
        else:
            print("  MACD: null")
    
    print("\nBollinger Bands:")
    if 'bb_upper' in indicators.get('bollinger', {}):
        upper = indicators['bollinger'].get('bb_upper')
        middle = indicators['bollinger'].get('bb_middle')
        lower = indicators['bollinger'].get('bb_lower')
        width = indicators['bollinger'].get('bb_width')
        if upper is not None:
            print(f"  Superior: {upper:.2f}")
            print(f"  Média: {middle:.2f}")
            print(f"  Inferior: {lower:.2f}")
            print(f"  Largura: {width:.4f}")
        else:
            print("  Bollinger Bands: null")
    
    print("\nATR:")
    if 'atr' in indicators.get('atr', {}):
        atr_val = indicators['atr'].get('atr')
        if atr_val is not None:
            print(f"  ATR 14: {atr_val:.2f}")
        else:
            print("  ATR 14: null")
    
    # Liquidações
    print("\n=== LIQUIDAÇÕES 24H ===")
    if 'liquidations' in market_data:
        liq = market_data['liquidations']
        print(f"Liquidações Long: {liq['long_liqs_24h']:,.2f} USDT")
        print(f"Liquidações Short: {liq['short_liqs_24h']:,.2f} USDT")
        print(f"Total Liquidações: {liq['total_liqs_24h']:,.2f} USDT")
        
        if liq['total_liqs_24h'] == 0:
            print("📊 Fonte: WebSocket em tempo real (sem liquidações no período)")
        else:
            print("📡 Fonte: WebSocket em tempo real")
    else:
        print("Liquidações: Não disponível (WebSocket desconectado)")
    
    if 'flow' in market_data:
        print("\n=== FLOW (CVD) ===")
        flow = market_data['flow']
        if flow['perp_cvd'] is not None:
            print(f"CVD Perpetual: {format_number(flow['perp_cvd'])} USDT")
            if flow['spot_cvd'] is not None:
                print(f"CVD Spot: {format_number(flow['spot_cvd'])} USDT")
            else:
                print("CVD Spot: Não disponível")
            print(f"Volume Perp Compra: {format_number(flow['perp_buy_volume_sample'])} USDT")
            print(f"Volume Perp Venda: {format_number(flow['perp_sell_volume_sample'])} USDT")
            if flow['spot_buy_volume_sample'] is not None:
                print(f"Volume Spot Compra: {format_number(flow['spot_buy_volume_sample'])} USDT")
                print(f"Volume Spot Venda: {format_number(flow['spot_sell_volume_sample'])} USDT")
        else:
            print("CVD: Não disponível")

def main():
    # Inicializa o coletor
    collector = MarketDataCollector()
    
    try:
        # Coleta os dados
        print("Coletando dados de mercado...")
        market_data = collector.collect_market_data()
        
        # Gera nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"market_data_{timestamp}.json"
        
        # Salva os dados
        collector.save_to_file(market_data, filename)
        print(f"\nDados salvos com sucesso em: {filename}")
        
        # Mostra o resumo completo
        print_market_summary(market_data)
        
    except Exception as e:
        print(f"\nErro ao coletar dados: {str(e)}")

if __name__ == "__main__":
    main() 