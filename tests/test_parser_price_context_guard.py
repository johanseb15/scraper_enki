from src.aplicacion.language_query_contract import PriceType
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_gpu_model_number_is_not_price():
    r=parse_pricing_query("cuánto sale una RTX 4060?")
    assert r.price.type==PriceType.UNKNOWN
    assert r.price.value is None
    assert r.device_type=="GPU"

def test_seat_quantity_is_not_price():
    r=parse_pricing_query("cuánto cuesta hacer cableado estructurado Cat6 para 15 puestos")
    assert r.price.type==PriceType.UNKNOWN
    assert r.price.value is None

def test_camera_quantity_is_not_price_without_amount():
    r=parse_pricing_query("instalar 4 cámaras IP")
    assert r.price.type==PriceType.UNKNOWN
    assert r.price.value is None

def test_memory_capacity_is_not_price():
    r=parse_pricing_query("notebook con 32GB de RAM")
    assert r.price.type==PriceType.UNKNOWN
    assert r.price.value is None

def test_naked_80_remains_unknown_currency_price():
    r=parse_pricing_query("80 por formatear en Córdoba")
    assert r.price.type==PriceType.EXACT
    assert r.price.value==80
    assert r.price.currency=="UNKNOWN"

def test_real_amount_before_camera_quantity_wins():
    r=parse_pricing_query("150.000 por instalar 4 cámaras IP")
    assert r.price.type==PriceType.EXACT
    assert r.price.value==150000
    assert r.price.currency=="UNKNOWN"

def test_temporal_guard_remains_intact():
    r=parse_pricing_query("precio de un SSD de hace 45 días")
    assert r.price.type==PriceType.UNKNOWN
    assert r.price.value is None
