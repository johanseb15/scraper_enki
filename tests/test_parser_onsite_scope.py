from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    MarketScope,
    ServiceModality,
)
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_domicilio_is_modality_when_concrete_service_exists():
    r=parse_pricing_query("cuánto sale formatear a domicilio en Córdoba?")
    assert r.canonical_services==("FORMATEO_INSTALACION_SO",)
    assert r.economic_object_kind==EconomicObjectKind.SERVICE
    assert r.is_bundle is False
    assert r.market_scope==MarketScope.LOCAL
    assert r.modality==ServiceModality.ONSITE
    assert r.metadata.clarification_required is False

def test_standalone_domicile_visit_remains_service():
    r=parse_pricing_query("cuánto cobra un técnico por ir a domicilio en zona oeste?")
    assert r.canonical_services==("VISITA_TECNICA_DOMICILIO",)
    assert r.economic_object_kind==EconomicObjectKind.SERVICE
    assert r.is_bundle is False
    assert r.market_scope==MarketScope.LOCAL
    assert r.modality==ServiceModality.ONSITE

def test_domicilio_does_not_hide_real_bundle():
    r=parse_pricing_query("formateo con backup a domicilio en Córdoba")
    assert r.canonical_services==("FORMATEO_INSTALACION_SO","BACKUP_DATOS")
    assert r.economic_object_kind==EconomicObjectKind.BUNDLE
    assert r.is_bundle is True
    assert r.modality==ServiceModality.ONSITE

def test_workshop_behavior_is_unchanged():
    r=parse_pricing_query("cuánto sale formatear en taller en Córdoba?")
    assert r.canonical_services==("FORMATEO_INSTALACION_SO",)
    assert r.modality==ServiceModality.WORKSHOP
