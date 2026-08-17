from src.aplicacion.language_query_contract import (
    IntentAction,
    IntentSide,
    PartsScope,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query


def test_solamente_de_mano_de_obra_is_labor_only():
    parsed = parse_pricing_query(
        "60 lucas solamente de mano de obra para cambiar una fuente, está bien?"
    )

    assert parsed.commercial_context.parts_scope == PartsScope.LABOR_ONLY


def test_me_piden_price_is_buy_evaluation():
    parsed = parse_pricing_query(
        "me piden 150 lucas por cambiar teclado de notebook, incluye el repuesto"
    )

    assert parsed.intent_action == IntentAction.EVALUATE_PRICE
    assert parsed.intent_side == IntentSide.BUY


def test_cuanto_puedo_cobrar_is_sell_suggestion():
    parsed = parse_pricing_query(
        "soy de zona oeste, cuanto puedo cobrar una visita técnica?"
    )

    assert parsed.intent_action == IntentAction.SUGGEST_PRICE
    assert parsed.intent_side == IntentSide.SELL


def test_cuanto_cobran_is_market_reference():
    parsed = parse_pricing_query(
        "cuánto cobran por armar pc?"
    )

    assert parsed.intent_action == IntentAction.MARKET_REFERENCE
