from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    IntentAction,
    MarketScope,
    ServiceModality,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_fullstack_development_maps_to_canonical_hourly_service():
    r=parse_pricing_query("cuánto se está cobrando la hora de desarrollo Fullstack Node/React?")
    assert r.canonical_services==("DESARROLLO_SOFTWARE_HORA",)
    assert r.economic_object_kind==EconomicObjectKind.SERVICE
    assert r.market_scope==MarketScope.REMOTE_NATIONAL
    assert r.modality==ServiceModality.REMOTE
    assert r.intent_action==IntentAction.MARKET_REFERENCE

def test_frontend_development_maps_to_same_canonical_service():
    r=parse_pricing_query("cuánto se cobra la hora de desarrollo frontend?")
    assert r.canonical_services==("DESARROLLO_SOFTWARE_HORA",)
    assert r.market_scope==MarketScope.REMOTE_NATIONAL

def test_backend_development_maps_to_same_canonical_service():
    r=parse_pricing_query("precio de referencia para desarrollo backend")
    assert r.canonical_services==("DESARROLLO_SOFTWARE_HORA",)
    assert r.economic_object_kind==EconomicObjectKind.SERVICE

def test_existing_desarrollo_web_rule_is_preserved():
    r=parse_pricing_query("cuánto sale desarrollo web por hora?")
    assert r.canonical_services==("DESARROLLO_SOFTWARE_HORA",)
