import pytest
import json
from datetime import datetime
from src.market_data_collector import MarketDataCollector

@pytest.fixture
def market_data():
    collector = MarketDataCollector()
    return collector.collect_market_data()

def test_required_fields(market_data):
    """Testa se todos os campos obrigatórios estão presentes"""
    required_fields = [
        'timestamp',
        'symbol',
        'current_price',
        'order_book',
        'derivatives',
        'stats',
        'timeframes'
    ]
    
    for field in required_fields:
        assert field in market_data, f"Campo obrigatório '{field}' não encontrado"

def test_timestamp_format(market_data):
    """Testa se o timestamp está no formato UTC ISO"""
    try:
        datetime.fromisoformat(market_data['timestamp'].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("Timestamp não está no formato ISO UTC")

def test_order_book_structure(market_data):
    """Testa a estrutura do order book"""
    order_book = market_data['order_book']
    
    assert 'top' in order_book
    assert 'depth_pct' in order_book
    
    # Verifica estrutura do top
    assert 'bids' in order_book['top']
    assert 'asks' in order_book['top']
    
    # Verifica profundidade
    assert 'bids' in order_book['depth_pct']
    assert 'asks' in order_book['depth_pct']
    
    for side in ['bids', 'asks']:
        for pct in ['0.5', '1.0', '2.0']:
            assert pct in order_book['depth_pct'][side]

def test_derivatives_data(market_data):
    """Testa os dados de derivativos"""
    derivatives = market_data['derivatives']
    
    required_fields = [
        'open_interest_usd',
        'open_interest_coin',
        'oi_change_4h_pct',
        'funding_rate',
        'funding_next'
    ]
    
    for field in required_fields:
        assert field in derivatives, f"Campo obrigatório '{field}' não encontrado em derivatives"

def test_volume_stats(market_data):
    """Testa as estatísticas de volume"""
    stats = market_data['stats']
    
    required_fields = [
        'volume_24h',
        'taker_buy_vol_24h',
        'taker_sell_vol_24h'
    ]
    
    for field in required_fields:
        assert field in stats, f"Campo obrigatório '{field}' não encontrado em stats"

def test_timeframes_data(market_data):
    """Testa os dados de timeframes"""
    timeframes = market_data['timeframes']
    
    required_timeframes = ['15m', '1h', '4h', '1d']
    for tf in required_timeframes:
        assert tf in timeframes, f"Timeframe '{tf}' não encontrado"
        
        # Verifica estrutura de cada timeframe
        tf_data = timeframes[tf]
        assert 'candles' in tf_data
        assert 'indicators' in tf_data
        
        # Verifica se tem 50 candles
        assert len(tf_data['candles']) == 50
        
        # Verifica indicadores
        indicators = tf_data['indicators']
        required_indicators = ['sma', 'ema', 'rsi', 'macd', 'bollinger', 'atr']
        for ind in required_indicators:
            assert ind in indicators, f"Indicador '{ind}' não encontrado"

def test_data_types(market_data):
    """Testa os tipos de dados dos campos numéricos"""
    assert isinstance(market_data['current_price'], float)
    assert isinstance(market_data['derivatives']['open_interest_usd'], float)
    assert isinstance(market_data['derivatives']['funding_rate'], float)
    assert isinstance(market_data['stats']['volume_24h'], float)

def test_json_serialization(market_data):
    """Testa se os dados podem ser serializados em JSON"""
    try:
        json.dumps(market_data)
    except TypeError as e:
        pytest.fail(f"Erro ao serializar JSON: {str(e)}") 