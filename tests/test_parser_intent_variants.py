from src.aplicacion.language_query_contract import IntentAction, MarketScope
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_cuanto_se_esta_cobrando_is_market_reference():
    r=parse_pricing_query("soporte remoto cuanto se esta cobrando la hora")
    assert r.intent_action==IntentAction.MARKET_REFERENCE
    assert r.market_scope==MarketScope.REMOTE_NATIONAL

def test_cuanto_estan_cobrando_is_market_reference():
    r=parse_pricing_query("en la plata cuanto estan cobrando el formateo de notebook")
    assert r.intent_action==IntentAction.MARKET_REFERENCE
    assert r.geography.province=="Buenos Aires"
    assert r.geography.city=="La Plata"

def test_cuanto_se_cobra_still_works():
    assert parse_pricing_query("cuanto se cobra soporte remoto").intent_action==IntentAction.MARKET_REFERENCE

def test_cuanto_sale_still_works():
    assert parse_pricing_query("cuanto sale formatear en Córdoba").intent_action==IntentAction.MARKET_REFERENCE
