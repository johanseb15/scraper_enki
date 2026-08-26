from __future__ import annotations

from src.aplicacion.language_query_contract import (
    IntentAction,
    IntentSide,
    PartsScope,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query


def test_rq029_buy_price_request_is_suggest_price():
    parsed = parse_pricing_query(
        "me ofrecieron una RTX 4060 usada, cu\u00e1nto deber\u00eda pagar?"
    )

    assert parsed.intent_side is IntentSide.BUY
    assert parsed.intent_action is IntentAction.SUGGEST_PRICE


def test_rq035_offer_with_price_and_conviene_is_evaluate_price():
    parsed = parse_pricing_query(
        "me ofrecen una notebook nueva a 1.5 palos, conviene?"
    )

    assert parsed.intent_action is IntentAction.EVALUATE_PRICE


def test_rq038_armar_la_pc_maps_to_armado_pc():
    parsed = parse_pricing_query(
        "cobrar 5% del valor de los componentes por armar la pc est\u00e1 bien?"
    )

    assert parsed.canonical_services == ("ARMADO_PC",)


def test_rq045_pc_then_armarla_maps_to_armado_pc():
    parsed = parse_pricing_query(
        "la pc vale m\u00e1s de 1 mill\u00f3n, "
        "me quieren cobrar entre 80 y 90k por armarla y tardan 4 horas"
    )

    assert parsed.canonical_services == ("ARMADO_PC",)


def test_rq046_estoy_cobrando_and_disk_aparte_means_sell_labor_only():
    parsed = parse_pricing_query(
        "estoy cobrando 40k de mano de obra por poner el SSD, "
        "el disco va aparte"
    )

    assert parsed.intent_side is IntentSide.SELL
    assert parsed.commercial_context.parts_scope is PartsScope.LABOR_ONLY
    assert parsed.canonical_services == ("UPGRADE_HARDWARE",)


# ------------------------------------------------------------------
# Negative boundaries: recover the five corpus cases without broadening
# unrelated language into economic/service claims.
# ------------------------------------------------------------------


def test_armarla_without_pc_context_does_not_invent_armado_pc():
    parsed = parse_pricing_query(
        "me trajeron una mesa y tengo que armarla"
    )

    assert "ARMADO_PC" not in parsed.canonical_services


def test_mano_de_obra_with_part_included_is_not_labor_only():
    parsed = parse_pricing_query(
        "cobro 40k de mano de obra e incluye el SSD"
    )

    assert parsed.commercial_context.parts_scope is not PartsScope.LABOR_ONLY


def test_me_ofrecen_without_price_question_does_not_invent_pricing_action():
    parsed = parse_pricing_query(
        "me ofrecen una notebook nueva"
    )

    assert parsed.intent_action is IntentAction.UNKNOWN
