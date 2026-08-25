from __future__ import annotations

import pytest
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.language_query_contract import EconomicObjectKind, IntentAction, IntentSide
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def resolve(query: str):
    return resolver_consulta_pricing(query, local_cohortes=(), remote_cohortes=())

@pytest.mark.parametrize("query",(
    "hice backup de 70gb, cambié el disco, instalé windows y después llevé la pc a la casa del cliente, cuanto le cobro?",
    "quiero cobrar instalación de ssd más clonado más limpieza, cuánto tendría que pedir?",
    "tengo que hacer backup de 70 GB y cambiar el disco, cuánto cobro?",
))
def test_true_multi_service_queries_become_terminal_bundles(query):
    parsed=parse_pricing_query(query)
    assert parsed.economic_object_kind is EconomicObjectKind.BUNDLE
    assert parsed.is_bundle is True
    assert "BUNDLE_REQUIRES_COMPARABLE_SCOPE" in (parsed.metadata.clarification_reason or "").split("|")
    result=resolve(query)
    assert result.status=="UNSUPPORTED_QUERY"
    assert result.unsupported_reason=="SINGLE_CANONICAL_SERVICE_REQUIRED"

def test_disk_change_and_cloning_is_one_composite_service_not_a_bundle():
    parsed=parse_pricing_query("me pasaron 80 mil por cambio de disco y clonado, está bien?")
    assert parsed.canonical_services==("CLONADO_DISCO",)
    assert parsed.economic_object_kind is EconomicObjectKind.SERVICE
    assert parsed.is_bundle is False

def test_user_provided_ssd_install_and_clone_remains_actionable_clarification():
    result=resolve("el cliente ya compró el ssd, cuánto le cobro por instalarlo y clonar?")
    assert result.parsed.canonical_services==("CLONADO_DISCO",)
    assert result.parsed.intent_action is IntentAction.SUGGEST_PRICE
    assert result.parsed.intent_side is IntentSide.SELL
    assert result.status=="CLARIFICATION_REQUIRED"

def test_explicit_ssd_labor_is_service_not_hardware_object():
    result=resolve("estoy cobrando 40k de mano de obra por poner el SSD, el disco va aparte")
    assert result.parsed.canonical_services==("UPGRADE_HARDWARE",)
    assert result.parsed.economic_object_kind is EconomicObjectKind.SERVICE
    assert result.status=="CLARIFICATION_REQUIRED"
