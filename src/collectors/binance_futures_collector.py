from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timezone, timedelta
from .base_collector import BaseCollector
from .websocket_liquidations import WebSocketLiquidationsCollector
from ..config import SYMBOL, ORDER_BOOK_LIMIT, DEPTH_LEVELS

class BinanceFuturesCollector(BaseCollector):
    def __init__(self):
        super().__init__('https://fapi.binance.com')
        self.symbol = SYMBOL
        
        # Inicializa WebSocket de liquidações
        self.ws_liquidations = WebSocketLiquidationsCollector(self.symbol)
        self.ws_liquidations.start_stream()

    def get_current_price(self) -> float:
        """Obtém o preço atual (mark price)"""
        data = self._make_request('/fapi/v1/premiumIndex', {'symbol': self.symbol})
        return float(data['markPrice'])

    def get_order_book(self) -> Dict:
        """Obtém o livro de ordens e calcula profundidade"""
        # Obtém mais níveis para calcular depth até ±2%
        data = self._make_request('/fapi/v1/depth', {
            'symbol': self.symbol,
            'limit': 500  # Aumentar para 500 níveis
        })

        # Processa o top do book (mantém apenas 20 para exibição)
        order_book = {
            'top': {
                'bids': [[float(price), float(qty)] for price, qty in data['bids'][:ORDER_BOOK_LIMIT]],
                'asks': [[float(price), float(qty)] for price, qty in data['asks'][:ORDER_BOOK_LIMIT]]
            }
        }

        # Calcula profundidade percentual usando todos os níveis disponíveis
        current_price = float(data['bids'][0][0])  # Preço do melhor bid
        depth_pct = {'bids': {}, 'asks': {}}

        for pct in DEPTH_LEVELS:
            # Calcula limites de preço para este percentual específico
            bid_limit = current_price * (1 - pct / 100)  # Limite inferior para bids
            ask_limit = current_price * (1 + pct / 100)  # Limite superior para asks
            
            # Calcula volume acumulado para bids (preços >= bid_limit)
            bid_volume = sum(
                float(qty) for price, qty in data['bids']
                if float(price) >= bid_limit
            )
            
            # Calcula volume acumulado para asks (preços <= ask_limit)
            ask_volume = sum(
                float(qty) for price, qty in data['asks']
                if float(price) <= ask_limit
            )
            
            depth_pct['bids'][str(pct)] = bid_volume
            depth_pct['asks'][str(pct)] = ask_volume

        # Calcula imbalance do order book (usando 1% de profundidade)
        total_bids_1pct = depth_pct['bids']['1.0']
        total_asks_1pct = depth_pct['asks']['1.0']
        total_volume = total_bids_1pct + total_asks_1pct
        
        if total_volume > 0:
            imbalance_pct = ((total_bids_1pct - total_asks_1pct) / total_volume) * 100
        else:
            imbalance_pct = 0

        order_book['depth_pct'] = depth_pct
        order_book['imbalance_pct'] = imbalance_pct
        return order_book

    def get_klines(self, interval: str, limit: int = 50) -> List[List]:
        """Obtém candles OHLCV"""
        data = self._make_request('/fapi/v1/klines', {
            'symbol': self.symbol,
            'interval': interval,
            'limit': limit
        })
        
        return [
            [
                float(candle[1]),  # open
                float(candle[2]),  # high
                float(candle[3]),  # low
                float(candle[4]),  # close
                float(candle[5]),  # volume
                int(candle[0])     # timestamp
            ]
            for candle in data
        ]

    def get_funding_rate(self) -> Dict:
        """Obtém taxa de funding atual e próxima"""
        data = self._make_request('/fapi/v1/premiumIndex', {'symbol': self.symbol})
        
        return {
            'funding_rate': float(data['lastFundingRate']),
            'funding_next': datetime.fromtimestamp(
                int(data['nextFundingTime']) / 1000,
                tz=timezone.utc
            ).isoformat()
        }

    def get_open_interest(self) -> Dict:
        """Obtém open interest atual e histórico"""
        # Obtém histórico de OI para calcular variação 4h
        oi_history = self._make_request('/futures/data/openInterestHist', {
            'symbol': self.symbol,
            'period': '5m',
            'limit': 49  # 4h = 48 períodos de 5m + 1 atual = 49
        })

        if len(oi_history) >= 2:
            current_oi = oi_history[-1]  # Mais recente
            oi_4h_ago = oi_history[0]    # 4h atrás
            
            current_value = float(current_oi['sumOpenInterest'])
            past_value = float(oi_4h_ago['sumOpenInterest'])
            
            # Calcula variação percentual
            if past_value > 0:
                oi_change_4h_pct = ((current_value - past_value) / past_value) * 100
            else:
                oi_change_4h_pct = 0
        else:
            # Se não tem dados suficientes
            current_oi = oi_history[-1] if oi_history else {'sumOpenInterest': '0'}
            current_value = float(current_oi['sumOpenInterest'])
            oi_change_4h_pct = 0

        current_price = self.get_current_price()
        
        return {
            'open_interest_usd': current_value * current_price,
            'open_interest_coin': current_value,
            'oi_change_4h_pct': oi_change_4h_pct
        }

    def get_volume_stats(self) -> Dict:
        """Obtém estatísticas de volume"""
        data = self._make_request('/fapi/v1/ticker/24hr', {'symbol': self.symbol})
        
        # Obtém volumes reais de compra/venda dos últimos trades
        try:
            buy_vol, sell_vol = self._get_buy_sell_volumes()
            # Se conseguiu obter dados reais, usa eles
            if buy_vol > 0 or sell_vol > 0:
                return {
                    'volume_24h': float(data['quoteVolume']),
                    'taker_buy_vol_24h': buy_vol,
                    'taker_sell_vol_24h': sell_vol
                }
        except:
            pass
        
        # Fallback: usa quoteVolume total e estima 50/50
        total_volume = float(data['quoteVolume'])
        return {
            'volume_24h': total_volume,
            'taker_buy_vol_24h': total_volume * 0.5,
            'taker_sell_vol_24h': total_volume * 0.5
        }

    def _get_buy_sell_volumes(self) -> tuple:
        """Calcula volumes de compra/venda baseado nos últimos trades"""
        # Obtém os últimos 1000 trades
        trades = self._make_request('/fapi/v1/aggTrades', {
            'symbol': self.symbol,
            'limit': 1000
        })
        
        buy_volume = 0
        sell_volume = 0
        
        for trade in trades:
            volume = float(trade['price']) * float(trade['qty'])
            if trade['m']:  # m = true significa que o comprador foi o market maker (venda)
                sell_volume += volume
            else:  # compra
                buy_volume += volume
        
        # Extrapola para 24h baseado na amostra
        total_sample_volume = buy_volume + sell_volume
        if total_sample_volume > 0:
            # Obtém volume total 24h
            ticker_data = self._make_request('/fapi/v1/ticker/24hr', {'symbol': self.symbol})
            total_24h = float(ticker_data['quoteVolume'])
            
            # Calcula proporção e extrapola
            buy_ratio = buy_volume / total_sample_volume
            sell_ratio = sell_volume / total_sample_volume
            
            return total_24h * buy_ratio, total_24h * sell_ratio
        
        return 0, 0

    def get_liquidations_24h(self) -> Dict:
        """Obtém liquidações agregadas das últimas 24h via WebSocket"""
        # Primeiro tenta WebSocket (tempo real)
        if not self.ws_liquidations.is_connected():
            # Aguarda conexão por até 5 segundos
            self.logger.info("Aguardando conexão WebSocket...")
            self.ws_liquidations.wait_for_connection(timeout=5)
        
        if self.ws_liquidations.is_connected():
            try:
                ws_data = self.ws_liquidations.get_liquidations_24h()
                
                # Se WebSocket tem dados, usa eles
                if ws_data['total_liqs_24h'] > 0:
                    self.logger.info(f"Liquidações obtidas via WebSocket: ${ws_data['total_liqs_24h']:,.2f}")
                    return ws_data
                else:
                    self.logger.info(f"WebSocket conectado mas sem liquidações de {self.symbol} nas últimas 24h")
                    # Retorna zeros em vez de None para mostrar que o sistema está funcionando
                    return {
                        'long_liqs_24h': 0.0,
                        'short_liqs_24h': 0.0,
                        'total_liqs_24h': 0.0
                    }
                    
            except Exception as e:
                self.logger.warning(f"Erro no WebSocket de liquidações: {e}")
        else:
            self.logger.warning("WebSocket de liquidações não conectado")
        
        # Se chegou aqui, WebSocket não está funcionando
        self.logger.info("Liquidações indisponíveis (WebSocket desconectado)")
        return None

    def get_cvd_data(self) -> Dict:
        """Calcula CVD (Cumulative Volume Delta) baseado nos trades"""
        try:
            # CVD Perpetual
            perp_trades = self._make_request('/fapi/v1/aggTrades', {
                'symbol': self.symbol,
                'limit': 1000
            })
            
            cvd_perp = 0
            perp_buy_volume = 0
            perp_sell_volume = 0
            
            for trade in perp_trades:
                price = float(trade['p'])
                qty = float(trade['q'])
                volume = price * qty
                
                if trade['m']:  # market maker = venda
                    perp_sell_volume += volume
                    cvd_perp -= volume
                else:  # compra
                    perp_buy_volume += volume
                    cvd_perp += volume
            
            # CVD Spot - usando API spot da Binance
            try:
                spot_trades = self._make_request_spot('/api/v3/aggTrades', {
                    'symbol': self.symbol,
                    'limit': 1000
                })
                
                cvd_spot = 0
                spot_buy_volume = 0
                spot_sell_volume = 0
                
                for trade in spot_trades:
                    price = float(trade['p'])
                    qty = float(trade['q'])
                    volume = price * qty
                    
                    if trade['m']:  # market maker = venda
                        spot_sell_volume += volume
                        cvd_spot -= volume
                    else:  # compra
                        spot_buy_volume += volume
                        cvd_spot += volume
                        
            except Exception:
                # Se não conseguir dados spot, define como null
                cvd_spot = None
                spot_buy_volume = None
                spot_sell_volume = None
            
            return {
                'perp_cvd': cvd_perp,
                'spot_cvd': cvd_spot,
                'perp_buy_volume_sample': perp_buy_volume,
                'perp_sell_volume_sample': perp_sell_volume,
                'spot_buy_volume_sample': spot_buy_volume,
                'spot_sell_volume_sample': spot_sell_volume
            }
            
        except Exception as e:
            self.logger.warning(f"Não foi possível calcular CVD: {str(e)}")
            return {
                'perp_cvd': None,
                'spot_cvd': None,
                'perp_buy_volume_sample': None,
                'perp_sell_volume_sample': None,
                'spot_buy_volume_sample': None,
                'spot_sell_volume_sample': None
            }

    def _make_request_spot(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """Faz requisição para API spot da Binance"""
        import requests
        response = requests.get(
            f"https://api.binance.com{endpoint}",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def __del__(self):
        """Cleanup ao destruir o objeto"""
        if hasattr(self, 'ws_liquidations'):
            self.ws_liquidations.stop_stream() 