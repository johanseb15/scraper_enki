from src.aplicacion.language_query_contract import IntentAction, IntentSide, EconomicObjectKind
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_me_dijeron_price_is_buy_evaluation():
    r=parse_pricing_query("me dijeron 110 lucas por un formateo con backup, te parece bien?")
    assert r.intent_side==IntentSide.BUY
    assert r.intent_action==IntentAction.EVALUATE_PRICE
    assert r.economic_object_kind==EconomicObjectKind.BUNDLE
    assert r.price.value==110000

def test_me_dijeron_price_without_judgment_still_evaluates_received_quote():
    r=parse_pricing_query("me dijeron 80 lucas por formatear la notebook")
    assert r.intent_side==IntentSide.BUY
    assert r.intent_action==IntentAction.EVALUATE_PRICE

def test_te_parece_bien_with_price_is_evaluation_even_without_side():
    r=parse_pricing_query("110 lucas por un formateo, te parece bien?")
    assert r.intent_action==IntentAction.EVALUATE_PRICE

def test_existing_me_cotizaron_stays_buy():
    r=parse_pricing_query("me cotizaron 50 lucas por soporte remoto")
    assert r.intent_side==IntentSide.BUY
    assert r.intent_action==IntentAction.EVALUATE_PRICE
