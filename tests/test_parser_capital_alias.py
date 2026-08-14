from src.aplicacion.language_query_contract import MarketScope
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_capital_alias_maps_to_caba():
    r=parse_pricing_query("20k por limpieza de PC en capital")
    assert r.geography.province=="CABA"
    assert r.canonical_services==("LIMPIEZA_MANTENIMIENTO",)
    assert r.market_scope==MarketScope.LOCAL

def test_capital_federal_still_maps_to_caba():
    r=parse_pricing_query("cuánto sale formatear en Capital Federal?")
    assert r.geography.province=="CABA"

def test_caba_explicit_still_maps_to_caba():
    r=parse_pricing_query("cuánto sale formatear en CABA?")
    assert r.geography.province=="CABA"

def test_capital_does_not_change_remote_market_scope():
    r=parse_pricing_query("soporte remoto desde capital")
    assert r.geography.province=="CABA"
    assert r.market_scope==MarketScope.REMOTE_NATIONAL
