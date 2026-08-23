from decimal import Decimal

import pytest

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_evidence_engine import CohortePricing
from src.aplicacion.pricing_dimensions import infer_commercial_context
from src.dominio.commercial_context import (
    CommercialContextCompatibility,
    CommercialContextOrigin,
    compare_commercial_contexts,
    commercial_context_from_value,
)
from src.infraestructura.real_world_query_tracer import trace_real_world_query


def _cohort(context: str) -> CohortePricing:
    return CohortePricing(
        market="AR",
        canonical_service="SOPORTE_REMOTO",
        observations_n=3,
        providers_n=3,
        min_ars=Decimal("28000"),
        q1_ars=Decimal("29000"),
        median_ars=Decimal("30000"),
        q3_ars=Decimal("35000"),
        max_ars=Decimal("40000"),
        spread_ratio=Decimal("1.428"),
        evidence_confidence="LOW",
        decision_ready=False,
        range_ready=True,
        price_scope="PER_HOUR",
        commercial_context=context,
    )


@pytest.mark.parametrize(
    ("query", "expected"),
    (
        ("cuanto se cobra por hora por soporte remoto en horario habitual?", "STANDARD"),
        ("cuanto se cobra por hora por soporte remoto de urgencia?", "URGENCY"),
        ("cuanto se cobra por hora por soporte remoto?", "UNKNOWN"),
        (
            "cuanto se cobra por hora por soporte remoto normal de urgencia?",
            "AMBIGUOUS",
        ),
    ),
)
def test_parser_resolves_typed_commercial_context_once(query, expected):
    parsed = parse_pricing_query(query, language_evidence_type="OBSERVED_USER")

    assert parsed.commercial_context.value.value == expected
    assert parsed.commercial_context.origin.value == "USER_CLAIM"
    assert parsed.commercial_context.raw_basis == (() if expected == "UNKNOWN" else parsed.commercial_context.raw_basis)


def test_urgency_parser_runtime_and_trace_share_one_context():
    query = "me quieren cobrar 48 lucas la hora por soporte remoto de urgencia, esta bien?"
    cohorts = (_cohort("STANDARD"), _cohort("URGENCY"))

    result = resolver_consulta_pricing(query, local_cohortes=(), remote_cohortes=cohorts)
    trace = trace_real_world_query(
        query,
        local_cohortes=(),
        remote_cohortes=cohorts,
        source_case_id="td004:red:urgency",
        case_origin="OBSERVED_USER",
    )

    assert result.parsed.commercial_context.value.value == "URGENCY"
    assert result.evidence.commercial_context.value.value == "URGENCY"
    assert trace.economic_dimensions["commercial_context"]["value"] == "URGENCY"
    assert trace.economic_dimensions["commercial_context"]["raw_basis"] == ["urgencia"]


def test_absent_user_context_does_not_default_to_standard_cohort():
    query = "cuanto se cobra por hora por soporte remoto?"

    result = resolver_consulta_pricing(
        query,
        local_cohortes=(),
        remote_cohortes=(_cohort("STANDARD"),),
    )

    assert result.parsed.commercial_context.value.value == "UNKNOWN"
    assert result.status == "NO_EVIDENCE"
    assert result.evidence.commercial_context.value.value == "UNKNOWN"


def test_ambiguous_user_context_is_not_compatible_with_standard_or_urgency():
    query = "cuanto se cobra por hora por soporte remoto normal de urgencia?"

    result = resolver_consulta_pricing(
        query,
        local_cohortes=(),
        remote_cohortes=(_cohort("STANDARD"), _cohort("URGENCY")),
    )

    assert result.parsed.commercial_context.value.value == "AMBIGUOUS"
    assert result.status == "NO_EVIDENCE"


def test_provider_context_uses_same_contract_with_distinct_provenance():
    source = infer_commercial_context("Atencion de urgencia fuera de horario")
    user = parse_pricing_query(
        "cuanto se cobra por hora por soporte remoto de urgencia?",
        language_evidence_type="OBSERVED_USER",
    ).commercial_context

    assert source.value is user.value
    assert source.origin is CommercialContextOrigin.SOURCE_CLAIM
    assert user.origin is CommercialContextOrigin.USER_CLAIM
    assert source.raw_basis
    assert user.raw_basis
    assert compare_commercial_contexts(source, user) is CommercialContextCompatibility.COMPATIBLE


def test_unknown_source_context_is_not_compatible_with_standard():
    unknown = infer_commercial_context("Hora de soporte remoto")
    standard = commercial_context_from_value(
        "STANDARD",
        origin=CommercialContextOrigin.SOURCE_CLAIM,
        raw_basis=("horario habitual",),
    )

    assert unknown.value.value == "UNKNOWN"
    assert compare_commercial_contexts(unknown, standard) is CommercialContextCompatibility.UNKNOWN_SIDE


@pytest.mark.parametrize("case_id", ("rq003", "rq032"))
def test_known_standard_urgency_regressions_preserve_unknown_without_default(case_id):
    queries = {
        "rq003": "quiero cobrar 30 lucas la hora de soporte remoto, me quedo corto?",
        "rq032": "me quieren cobrar 35 lucas la hora por soporte remoto, esta bien?",
    }

    result = resolver_consulta_pricing(
        queries[case_id],
        local_cohortes=(),
        remote_cohortes=(_cohort("STANDARD"), _cohort("URGENCY")),
    )

    assert result.parsed.commercial_context.value.value == "UNKNOWN"
    assert result.status == "NO_EVIDENCE"
