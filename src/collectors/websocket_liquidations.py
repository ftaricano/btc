import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import websocket

class WebSocketLiquidationsCollector:
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol.lower()
        self.logger = logging.getLogger(__name__)
        
        # Armazenamento das liquidações
        self.liquidations_24h = {
            'long_liqs': 0,
            'short_liqs': 0,
            'total_liqs': 0,
            'last_reset': datetime.now()
        }
        
        # WebSocket
        self.ws = None
        self.is_running = False
        self.thread = None
        
        # Lock para thread safety
        self.lock = threading.Lock()

    def start_stream(self):
        """Inicia o stream de liquidações"""
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.thread.start()
        self.logger.info("Stream de liquidações iniciado")

    def stop_stream(self):
        """Para o stream de liquidações"""
        self.is_running = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Stream de liquidações parado")

    def _run_websocket(self):
        """Executa o WebSocket em thread separada"""
        websocket.enableTrace(False)
        
        # URL do WebSocket público da Binance para liquidações
        ws_url = "wss://fstream.binance.com/ws/!forceOrder@arr"
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        # Reconecta automaticamente se desconectar
        while self.is_running:
            try:
                self.ws.run_forever()
                if self.is_running:
                    self.logger.warning("WebSocket desconectado, reconectando em 5s...")
                    time.sleep(5)
            except Exception as e:
                self.logger.error(f"Erro no WebSocket: {e}")
                if self.is_running:
                    time.sleep(5)

    def _on_open(self, ws):
        """Callback quando WebSocket conecta"""
        self.logger.info("WebSocket de liquidações conectado")

    def _on_close(self, ws, close_status_code=None, close_msg=None):
        """Callback quando WebSocket é fechado"""
        self.logger.info("Stream de liquidações parado")
        self.is_running = False

    def _on_error(self, ws, error):
        """Callback para erros do WebSocket"""
        self.logger.error(f"Erro no WebSocket: {error}")

    def _on_message(self, ws, message):
        """Processa mensagens de liquidação"""
        try:
            data = json.loads(message)
            
            # Log para debug
            self.logger.debug(f"Mensagem recebida: {data}")
            
            # Extrai dados da liquidação
            order_data = data.get('o', {})
            symbol = order_data.get('s', '')
            
            # Verifica se é uma liquidação do nosso símbolo OU se queremos todas
            if symbol == self.symbol.upper() or self.symbol.upper() == 'ALL':
                self.logger.info(f"Liquidação detectada para {symbol}: {order_data}")
                self._process_liquidation(order_data, symbol)
            else:
                # Log de símbolos diferentes para debug
                if symbol:
                    self.logger.debug(f"Liquidação de outro símbolo ignorada: {symbol}")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar liquidação: {e}")

    def _process_liquidation(self, liquidation_data, symbol=None):
        """Processa uma liquidação individual"""
        try:
            side = liquidation_data.get('S')  # BUY ou SELL
            price = float(liquidation_data.get('ap', 0))  # Average price
            qty = float(liquidation_data.get('q', 0))
            
            # Calcula valor em USDT
            value_usd = price * qty
            
            self.logger.info(f"Processando liquidação {symbol or self.symbol}: {side} {qty:.4f} @ {price:.2f} = ${value_usd:.2f}")
            
            with self.lock:
                # Reseta contadores se passou 24h
                self._reset_if_needed()
                
                # Adiciona à contagem
                if side == 'SELL':  # Liquidação de posição long
                    self.liquidations_24h['long_liqs'] += value_usd
                    self.logger.info(f"Liquidação LONG adicionada: +${value_usd:.2f} (Total: ${self.liquidations_24h['long_liqs']:.2f})")
                elif side == 'BUY':  # Liquidação de posição short
                    self.liquidations_24h['short_liqs'] += value_usd
                    self.logger.info(f"Liquidação SHORT adicionada: +${value_usd:.2f} (Total: ${self.liquidations_24h['short_liqs']:.2f})")
                
                self.liquidations_24h['total_liqs'] = (
                    self.liquidations_24h['long_liqs'] + 
                    self.liquidations_24h['short_liqs']
                )
                
        except Exception as e:
            self.logger.error(f"Erro ao processar liquidação: {e}")

    def _reset_if_needed(self):
        """Reseta contadores se passou 24h"""
        now = datetime.now()
        if now - self.liquidations_24h['last_reset'] > timedelta(hours=24):
            self.liquidations_24h = {
                'long_liqs': 0,
                'short_liqs': 0,
                'total_liqs': 0,
                'last_reset': now
            }
            self.logger.info("Contadores de liquidação resetados (24h)")

    def get_liquidations_24h(self) -> Dict:
        """Retorna liquidações acumuladas das últimas 24h"""
        with self.lock:
            self._reset_if_needed()
            
            # Log do estado atual
            self.logger.debug(f"Estado atual das liquidações: Long=${self.liquidations_24h['long_liqs']:.2f}, "
                            f"Short=${self.liquidations_24h['short_liqs']:.2f}, "
                            f"Total=${self.liquidations_24h['total_liqs']:.2f}")
            
            return {
                'long_liqs_24h': self.liquidations_24h['long_liqs'],
                'short_liqs_24h': self.liquidations_24h['short_liqs'],
                'total_liqs_24h': self.liquidations_24h['total_liqs']
            }

    def is_connected(self) -> bool:
        """Verifica se o WebSocket está conectado"""
        try:
            return (self.is_running and 
                   self.ws and 
                   hasattr(self.ws, 'sock') and 
                   self.ws.sock and 
                   self.ws.sock.connected)
        except:
            return False

    def wait_for_connection(self, timeout: int = 10) -> bool:
        """Aguarda conexão por até timeout segundos"""
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_connected():
                return True
            time.sleep(0.1)
        return False 