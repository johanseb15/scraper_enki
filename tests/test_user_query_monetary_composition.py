from fastapi.testclient import TestClient

from src.api.main import app
from src.aplicacion.parser_consulta_pricing import (
    parse_pricing_query,
)
from src.aplicacion.pricing_cohort_loader import (
    cargar_cohortes_pricing_runtime,
)
from src.aplicacion.user_query_understanding_projector import (
    project_user_query_understanding,
)
from src.aplicacion.user_query_understanding_serializer import (
    serialize_user_query_understanding,
)
from src.dominio.real_world_query_trace import InputModality
from src.infraestructura.real_world_query_tracer import (
    trace_real_world_query,
)


HUMAN_REAL_COMPOSITION_QUERY = (
    "Cuanto cobran, mano de obra + pendrive de 64gb "
    "(sale 25.000) = backup? Yo cobre 65.000, "
    "pendrive + mano de obra y ya le queda un pendrive "
    "con toda su info"
)


def test_human_real_query_preserves_total_material_and_derived_labor():
    parsed = parse_pricing_query(
        HUMAN_REAL_COMPOSITION_QUERY,
        language_evidence_type="OBSERVED_USER",
    )

    assert parsed.price.value == 65_000
    assert parsed.price.raw_expression == "65.000"
    assert parsed.intent_action.value == "EVALUATE_PRICE"
    assert parsed.intent_side.value == "SELL"

    components = {
        item.role.value: item
        for item in parsed.monetary_components
    }

    assert components["TOTAL_CHARGED"].value == 65_000
    assert components["TOTAL_CHARGED"].origin.value == "EXPLICIT"
    assert components["TOTAL_CHARGED"].raw_expression == "65.000"

    assert components["MATERIAL_COST"].value == 25_000
    assert components["MATERIAL_COST"].origin.value == "EXPLICIT"
    assert components["MATERIAL_COST"].raw_expression == "25.000"

    assert components["LABOR"].value == 40_000
    assert components["LABOR"].origin.value == "DERIVED"
    assert components["LABOR"].raw_expression is None
    assert components["LABOR"].derivation_method == (
        "TOTAL_CHARGED_MINUS_MATERIAL_COST"
    )

    assert parsed.price.currency == "UNKNOWN"
    assert parsed.metadata.clarification_required is True
    assert "MULTIPLE_MONETARY_MENTIONS" in (
        parsed.metadata.clarification_reason or ""
    )
    assert "UNKNOWN_CURRENCY" in (
        parsed.metadata.clarification_reason or ""
    )


def test_monetary_composition_is_projected_with_origins_and_relations():
    parsed = parse_pricing_query(
        HUMAN_REAL_COMPOSITION_QUERY,
        language_evidence_type="OBSERVED_USER",
    )

    envelope = project_user_query_understanding(
        parsed,
    )

    facts = {
        item.field: item
        for item in envelope.facts
    }

    assert facts[
        "monetary_component.total_charged"
    ].origin.value == "EXPLICIT"

    assert facts[
        "monetary_component.material_cost"
    ].origin.value == "EXPLICIT"

    assert facts[
        "monetary_component.labor"
    ].origin.value == "DERIVED"

    assert facts[
        "monetary_component.labor"
    ].value["amount"] == 40_000

    relations = {
        (
            item.subject,
            item.predicate,
            item.object,
        )
        for item in envelope.relations
    }

    assert (
        "TOTAL_CHARGED",
        "INCLUDES_COMPONENT",
        "MATERIAL_COST",
    ) in relations

    assert (
        "TOTAL_CHARGED",
        "INCLUDES_COMPONENT",
        "LABOR",
    ) in relations

    serialized = serialize_user_query_understanding(
        envelope,
    )

    assert serialized["schema_version"] == (
        "user-query-understanding-trace-v1"
    )

    assert (
        envelope.projection_provenance.origin_version
        == "user-query-understanding-v2"
    )

    serialized_facts = {
        item["field"]: item
        for item in serialized["facts"]
    }

    assert serialized_facts[
        "monetary_component.material_cost"
    ]["value"]["raw_expression"] == "25.000"

    assert serialized_facts[
        "monetary_component.labor"
    ]["value"]["derived_from"] == [
        "TOTAL_CHARGED",
        "MATERIAL_COST",
    ]


def test_independent_prices_are_not_silently_decomposed():
    parsed = parse_pricing_query(
        "me cobran 15 lucas de viatico mas 20k "
        "por hora de soporte remoto"
    )

    assert parsed.monetary_components == ()
    assert "MULTIPLE_MONETARY_MENTIONS" in (
        parsed.metadata.clarification_reason or ""
    )


def test_negative_labor_component_is_never_derived():
    parsed = parse_pricing_query(
        "mano de obra + pendrive de 64gb "
        "(sale 65.000); yo cobre 25.000 por el backup"
    )

    components = {
        item.role.value: item
        for item in parsed.monetary_components
    }

    assert components["TOTAL_CHARGED"].value == 25_000
    assert components["MATERIAL_COST"].value == 65_000
    assert "LABOR" not in components


def test_explicit_ars_composition_preserves_currency():
    parsed = parse_pricing_query(
        "mano de obra + pendrive (sale $25.000); "
        "yo cobre $65.000 por el backup"
    )

    components = {
        item.role.value: item
        for item in parsed.monetary_components
    }

    assert parsed.price.value == 65_000
    assert parsed.price.currency == "ARS"
    assert components["TOTAL_CHARGED"].currency == "ARS"
    assert components["MATERIAL_COST"].currency == "ARS"
    assert components["LABOR"].value == 40_000
    assert components["LABOR"].currency == "ARS"


def test_currency_conflict_prevents_derived_labor():
    parsed = parse_pricing_query(
        "mano de obra + pendrive (sale 25 USD); "
        "yo cobre $65.000 por el backup"
    )

    components = {
        item.role.value: item
        for item in parsed.monetary_components
    }

    assert components["TOTAL_CHARGED"].currency == "ARS"
    assert components["MATERIAL_COST"].currency == "USD"
    assert "LABOR" not in components


def test_single_price_query_has_no_fabricated_composition():
    parsed = parse_pricing_query(
        "me quieren cobrar 35 lucas la hora "
        "por soporte remoto, esta bien?"
    )

    assert parsed.monetary_components == ()


def test_composition_reaches_trace_without_authorizing_decision_or_promotion():
    local, remote = cargar_cohortes_pricing_runtime()

    trace = trace_real_world_query(
        HUMAN_REAL_COMPOSITION_QUERY,
        local_cohortes=local,
        remote_cohortes=remote,
        source_case_id="block-c-monetary-composition",
        case_origin="OBSERVED_USER",
        input_modality=InputModality.TEXT,
    )

    facts = {
        item["field"]: item
        for item in trace.semantic_result["facts"]
    }

    assert facts[
        "monetary_component.total_charged"
    ]["value"]["amount"] == 65_000

    assert facts[
        "monetary_component.labor"
    ]["value"]["amount"] == 40_000

    assert trace.readiness == "CLARIFICATION_REQUIRED"
    assert trace.accepted_evidence == ()
    assert trace.runtime_mutation is False
    assert trace.promotion_authorized is False


def test_public_api_uses_total_but_remains_fail_closed():
    response = TestClient(app).post(
        "/decision/pricing",
        json={
            "query": HUMAN_REAL_COMPOSITION_QUERY,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "CLARIFICATION_REQUIRED"
    assert body["parsed"]["price"]["value"] == 65_000
    assert body["parsed"]["intent_action"] == "EVALUATE_PRICE"
    assert body["parsed"]["intent_side"] == "SELL"

    components = {
        item["role"]: item
        for item in body["parsed"]["monetary_components"]
    }

    assert components["TOTAL_CHARGED"]["value"] == 65_000
    assert components["MATERIAL_COST"]["value"] == 25_000
    assert components["LABOR"]["value"] == 40_000
    assert components["LABOR"]["origin"] == "DERIVED"
    assert components["LABOR"]["derived_from"] == [
        "TOTAL_CHARGED",
        "MATERIAL_COST",
    ]

    assert body["evidence"] is None
