from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    IntentAction,
    IntentSide,
    MarketScope,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

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
