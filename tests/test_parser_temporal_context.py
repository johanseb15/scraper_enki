from src.aplicacion.language_query_contract import EconomicObjectKind, MarketScope, PriceType
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_days_are_not_parsed_as_price():
    r=parse_pricing_query("tengo un precio de un disco SSD de hace 45 días")
    assert r.price.type==PriceType.UNKNOWN
    assert r.price.value is None
    assert r.price.currency=="UNKNOWN"
    assert r.economic_object_kind==EconomicObjectKind.HARDWARE
    assert r.market_scope==MarketScope.GOODS
    assert r.metadata.clarification_required is False

def test_months_are_not_parsed_as_price():
    r=parse_pricing_query("vi esta notebook hace 12 meses")
    assert r.price.type==PriceType.UNKNOWN
    assert r.price.value is None

def test_naked_money_like_number_still_requires_currency():
    r=parse_pricing_query("80 por formatear en Córdoba está bien?")
    assert r.price.value==80
    assert r.price.currency=="UNKNOWN"
    assert r.metadata.clarification_required is True


def test_accented_years_are_not_parsed_as_price():
    r=parse_pricing_query("esa notebook tiene 2 años de uso")
    assert r.price.type==PriceType.UNKNOWN
    assert r.price.value is None
