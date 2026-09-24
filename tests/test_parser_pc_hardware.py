import json
from pathlib import Path

from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    IntentAction,
    IntentSide,
    MarketScope,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.user_query_understanding_projector import (
    project_user_query_understanding,
)

def test_quoted_complete_pc_is_hardware_goods():
    r=parse_pricing_query("me cotizaron $950.000 una PC para diseño gráfico")
    assert r.economic_object_kind==EconomicObjectKind.HARDWARE
    assert r.market_scope==MarketScope.GOODS
    assert r.device_type=="PC"
    assert r.intent_side==IntentSide.BUY
    assert r.intent_action==IntentAction.EVALUATE_PRICE

def test_pc_with_specs_is_hardware_goods():
    r=parse_pricing_query("cuánto sale una PC con Ryzen 7 y 32GB de RAM?")
    assert r.economic_object_kind==EconomicObjectKind.HARDWARE
    assert r.market_scope==MarketScope.GOODS
    assert r.device_type=="PC"

def test_pc_mentioned_as_service_device_is_not_reclassified_as_hardware():
    r=parse_pricing_query("me cobran $25.000 por reinstalar el WhatsApp Web y configurar el correo en mi compu")
    assert r.economic_object_kind!=EconomicObjectKind.HARDWARE

def test_existing_pc_armada_hardware_behavior_is_preserved():
    r=parse_pricing_query("cuánto sale una pc armada nueva?")
    assert r.economic_object_kind==EconomicObjectKind.HARDWARE
    assert r.market_scope==MarketScope.GOODS

def test_pc_with_specs_preserves_hardware_composition():
    r = parse_pricing_query(
        "cuánto sale una PC con Ryzen 7 y 32GB de RAM?"
    )

    assert r.hardware_composition is not None
    assert r.hardware_composition.families == (
        "CPU",
        "MEMORY",
    )
    assert r.hardware_composition.spec_signals == (
        "32GB",
    )

def test_hardware_without_composition_keeps_composition_unknown():
    r = parse_pricing_query("cuánto sale una pc armada nueva?")
    assert r.hardware_composition is None


def test_service_device_does_not_create_hardware_composition():
    r = parse_pricing_query("quiero cobrar por formatear una notebook")
    assert r.hardware_composition is None


def test_web_real_006_preserves_commercial_goods_bundle_and_pc_composition():
    corpus = Path("data/language/observed_user_raw_v1.jsonl")
    row = next(
        json.loads(line)
        for line in corpus.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["metadata"]["legacy_case_id"] == "WEB_REAL_006"
    )

    parsed = parse_pricing_query(row["raw_text"])

    assert parsed.economic_object_kind is EconomicObjectKind.BUNDLE
    assert parsed.is_bundle is True
    assert parsed.goods_components == ("PC", "MONITOR", "MOUSE")
    assert parsed.price.value == 580_000
    assert parsed.price.currency == "ARS"
    assert parsed.canonical_services == ()
    assert parsed.hardware_composition is not None
    assert parsed.hardware_composition.families == (
        "CPU", "GPU", "MEMORY", "STORAGE", "PSU"
    )
    assert parsed.condition == "UNKNOWN"

    facts = {
        fact.field: fact.value
        for fact in project_user_query_understanding(parsed).facts
    }
    assert facts["goods_components"] == ("PC", "MONITOR", "MOUSE")


def test_explicit_pc_plus_peripherals_is_goods_bundle():
    parsed = parse_pricing_query("PC + monitor + mouse por $580.000")

    assert parsed.economic_object_kind is EconomicObjectKind.BUNDLE
    assert parsed.is_bundle is True
    assert parsed.goods_components == ("PC", "MONITOR", "MOUSE")
    assert parsed.canonical_services == ()


def test_monitor_priced_separately_does_not_enter_pc_quote():
    parsed = parse_pricing_query(
        "Me cotizaron una PC con Ryzen 7 por $500.000. "
        "Incluye armado; el monitor se paga aparte."
    )

    assert parsed.economic_object_kind is EconomicObjectKind.HARDWARE
    assert parsed.is_bundle is False
    assert parsed.goods_components == ()


def test_todo_does_not_link_unrelated_peripherals_to_pc_quote():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC con Ryzen 7 por $500.000. "
        "El monitor ya lo tengo y el mouse también. Todo funciona bien."
    )

    assert parsed.economic_object_kind is EconomicObjectKind.HARDWARE
    assert parsed.is_bundle is False
    assert parsed.goods_components == ()


def test_unrelated_mouse_is_not_added_to_explicit_pc_monitor_bundle():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC que incluye monitor por $500.000. "
        "El mouse ya lo tengo."
    )

    assert parsed.economic_object_kind is EconomicObjectKind.BUNDLE
    assert parsed.is_bundle is True
    assert parsed.goods_components == ("PC", "MONITOR")


def test_mouse_mentioned_before_inclusion_is_not_a_bundle_member():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC; el mouse ya lo tengo, "
        "pero la PC incluye monitor por $500.000."
    )

    assert parsed.economic_object_kind is EconomicObjectKind.BUNDLE
    assert parsed.goods_components == ("PC", "MONITOR")


def test_separate_mouse_does_not_cancel_pc_monitor_bundle():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC que incluye monitor por $500.000. "
        "El mouse se paga aparte."
    )

    assert parsed.economic_object_kind is EconomicObjectKind.BUNDLE
    assert parsed.is_bundle is True
    assert parsed.goods_components == ("PC", "MONITOR")


def test_separate_only_peripheral_leaves_no_goods_bundle_members():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC con Ryzen 7 que incluye monitor por $500.000, "
        "pero el monitor se paga aparte."
    )

    assert parsed.is_bundle is False
    assert parsed.goods_components == ()
