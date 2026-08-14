from src.aplicacion.language_query_contract import PriceType
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_usd_monthly_is_per_month():
    r=parse_pricing_query("80 dólares por el soporte remoto mensual, es lógico?")
    assert r.price.currency=="USD"
    assert r.price.type==PriceType.PER_MONTH
    assert r.price.value==80

def test_usd_per_hour_is_per_hour():
    r=parse_pricing_query("50 USD por hora de soporte remoto")
    assert r.price.currency=="USD"
    assert r.price.type==PriceType.PER_HOUR
    assert r.price.value==50

def test_usd_plain_amount_stays_exact():
    r=parse_pricing_query("80 dólares por soporte remoto")
    assert r.price.currency=="USD"
    assert r.price.type==PriceType.EXACT

def test_ars_monthly_behavior_is_unchanged():
    r=parse_pricing_query("50 lucas al mes por soporte remoto")
    assert r.price.currency=="ARS"
    assert r.price.type==PriceType.PER_MONTH
