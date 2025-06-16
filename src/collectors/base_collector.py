import time
import requests
from typing import Dict, Any, Optional
import logging
from ..config import MAX_RETRIES, INITIAL_BACKOFF, MAX_BACKOFF

class BaseCollector:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Faz uma requisição HTTP com retry exponencial em caso de rate limit
        """
        backoff = INITIAL_BACKOFF
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 429:  # Rate limit
                    if attempt < MAX_RETRIES - 1:
                        self.logger.warning(f"Rate limit atingido. Tentativa {attempt + 1}/{MAX_RETRIES}")
                        time.sleep(backoff)
                        backoff = min(backoff * 2, MAX_BACKOFF)
                        continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    self.logger.error(f"Erro na requisição após {MAX_RETRIES} tentativas: {str(e)}")
                    raise
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
        
        raise Exception("Número máximo de tentativas excedido")

    def get_current_price(self) -> float:
        """Método base para obter preço atual"""
        raise NotImplementedError

    def get_order_book(self) -> Dict:
        """Método base para obter livro de ordens"""
        raise NotImplementedError

    def get_klines(self, interval: str, limit: int = 50) -> list:
        """Método base para obter candles"""
        raise NotImplementedError

    def get_funding_rate(self) -> Dict:
        """Método base para obter taxa de funding"""
        raise NotImplementedError

    def get_open_interest(self) -> Dict:
        """Método base para obter open interest"""
        raise NotImplementedError 