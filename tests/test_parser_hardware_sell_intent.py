from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    IntentAction,
    IntentSide,
    MarketScope,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_want_to_sell_used_notebook_maps_to_sell_suggestion():
    r=parse_pricing_query("quiero vender mi notebook usada")
    assert r.economic_object_kind==EconomicObjectKind.HARDWARE
    assert r.market_scope==MarketScope.GOODS
    assert r.intent_side==IntentSide.SELL
    assert r.intent_action==IntentAction.SUGGEST_PRICE
    assert r.condition=="USED"
    assert r.device_type=="NOTEBOOK"

def test_sell_notebook_with_price_becomes_evaluation():
    r=parse_pricing_query("quiero vender mi notebook usada a 500 lucas, está bien?")
    assert r.intent_side==IntentSide.SELL
    assert r.intent_action==IntentAction.EVALUATE_PRICE
    assert r.economic_object_kind==EconomicObjectKind.HARDWARE

def test_vendo_notebook_is_sell_side():
    r=parse_pricing_query("vendo notebook usada, cuánto pedir?")
    assert r.intent_side==IntentSide.SELL
    assert r.economic_object_kind==EconomicObjectKind.HARDWARE
    assert r.condition=="USED"

def test_service_sell_intent_stays_service():
    r=parse_pricing_query("quiero cobrar por formatear una notebook")
    assert r.intent_side==IntentSide.SELL
    assert r.economic_object_kind==EconomicObjectKind.SERVICE
