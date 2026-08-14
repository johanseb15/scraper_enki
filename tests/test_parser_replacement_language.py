from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    PartsScope,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_cambiar_teclado_maps_to_hardware_repair():
    r=parse_pricing_query("me quieren cobrar 50 lucas por cambiar un teclado de notebook, está bien?")
    assert r.economic_object_kind==EconomicObjectKind.SERVICE
    assert r.canonical_services==("REPARACION_HARDWARE",)
    assert r.commercial_context.parts_scope==PartsScope.UNKNOWN
    assert r.metadata.clarification_required is True
    assert "UNKNOWN_PARTS_SCOPE" in (r.metadata.clarification_reason or "")

def test_cambio_de_fuente_maps_to_hardware_repair():
    r=parse_pricing_query("60k por el cambio de fuente, está bien?")
    assert r.economic_object_kind==EconomicObjectKind.SERVICE
    assert r.canonical_services==("REPARACION_HARDWARE",)
    assert r.commercial_context.parts_scope==PartsScope.UNKNOWN
    assert r.metadata.clarification_required is True
    assert "UNKNOWN_PARTS_SCOPE" in (r.metadata.clarification_reason or "")

def test_explicit_labor_only_suppresses_parts_scope_ambiguity():
    r=parse_pricing_query("50 lucas solo mano de obra por cambiar un teclado en CABA")
    assert r.canonical_services==("REPARACION_HARDWARE",)
    assert r.commercial_context.parts_scope==PartsScope.LABOR_ONLY
    assert "UNKNOWN_PARTS_SCOPE" not in (r.metadata.clarification_reason or "")

def test_existing_screen_replacement_stays_supported():
    r=parse_pricing_query("me cobran 95 lucas por cambio de pantalla en CABA")
    assert r.canonical_services==("REPARACION_HARDWARE",)
