from __future__ import annotations
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing

def resolve(q: str):
    return resolver_consulta_pricing(q, local_cohortes=(), remote_cohortes=())

def test_explicit_bundle_terminal_fact_precedes_clarification():
    r = resolve("cuanto cobrar por limpiar la máquina, sacarle virus, instalar windows y todos los programas?")
    assert r.status == "UNSUPPORTED_QUERY"
    assert r.unsupported_reason == "SINGLE_CANONICAL_SERVICE_REQUIRED"
    assert r.clarification_reason is None

def test_explicit_unsupported_currency_precedes_clarification():
    r = resolve("me quieren cobrar 200 USDT por soporte remoto")
    assert r.status == "UNSUPPORTED_QUERY"
    assert r.unsupported_reason == "ARS_ONLY_V1"
    assert r.clarification_reason is None

def test_missing_currency_remains_clarification():
    assert resolve("80 por soporte remoto está bien?").status == "CLARIFICATION_REQUIRED"

def test_generic_missing_information_remains_clarification():
    assert resolve("Necesito formatear una PC").status == "CLARIFICATION_REQUIRED"
    assert resolve("cuánto cobrar por formatear una notebook?").status == "CLARIFICATION_REQUIRED"

def test_incomplete_parser_bundle_families_remain_for_td006():
    for q in (
        "hice backup de 70gb, cambié el disco, instalé windows y después llevé la pc a la casa del cliente, cuanto le cobro?",
        "quiero cobrar instalación de ssd más clonado más limpieza, cuánto tendría que pedir?",
        "tengo que hacer backup de 70 GB y cambiar el disco, cuánto cobro?",
    ):
        assert resolve(q).status == "CLARIFICATION_REQUIRED"

def test_non_actionable_fragment_keeps_existing_terminal_behavior():
    r = resolve("remoto por TeamViewer")
    assert r.status == "UNSUPPORTED_QUERY"
    assert r.unsupported_reason == "UNSUPPORTED_INTENT"
