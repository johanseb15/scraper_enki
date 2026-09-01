from dataclasses import asdict

from src.aplicacion.enki_pricing_query_service import (
    resolver_consulta_pricing,
)
from src.aplicacion.enki_pricing_response import (
    presentar_resultado_pricing,
)
from src.aplicacion.parser_consulta_pricing import (
    parse_pricing_query,
)
from src.aplicacion.pricing_cohort_loader import (
    cargar_cohortes_pricing_runtime,
)
from src.dominio.real_world_query_trace import InputModality
from src.infraestructura.real_world_query_tracer import (
    trace_real_world_query,
)


def _trace(raw):
    local, remote = cargar_cohortes_pricing_runtime()

    return trace_real_world_query(
        raw,
        local_cohortes=local,
        remote_cohortes=remote,
        source_case_id="block-b-test",
        case_origin="OBSERVED_USER",
        input_modality=InputModality.TEXT,
    )


def test_trace_semantic_result_contains_user_understanding_envelope():
    trace = _trace(
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    semantic = trace.semantic_result

    assert semantic["schema_version"] == (
        "user-query-understanding-trace-v1"
    )

    assert semantic["context"] == "USER_QUERY"
    assert semantic["status"] == "REPRESENTED"

    facts = {
        item["field"]: item
        for item in semantic["facts"]
    }

    assert facts["canonical_services"]["value"] == [
        "FORMATEO_INSTALACION_SO"
    ]

    assert facts["market_scope"]["value"] == "LOCAL"
    assert facts["modality"]["value"] == "ONSITE"
    assert facts["geography.province"]["value"] == "CABA"

    assert semantic["unknowns"] == []


def test_trace_preserves_fact_origin_and_provenance_chain():
    trace = _trace(
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    semantic = trace.semantic_result

    facts = {
        item["field"]: item
        for item in semantic["facts"]
    }

    assert facts["modality"]["origin"] == "EXPLICIT"

    assert (
        facts["canonical_services"]["origin"]
        == "DERIVED"
    )

    assert (
        semantic["raw_provenance"]["origin_type"]
        == "OBSERVED_USER"
    )

    assert (
        semantic["interpretation_provenance"]["origin_type"]
        == "PRICING_QUERY_PARSER"
    )

    assert (
        semantic["projection_provenance"]["origin_type"]
        == "USER_QUERY_UNDERSTANDING_PROJECTOR"
    )


def test_trace_unknown_query_remains_fail_closed():
    trace = _trace(
        "necesito ayuda con algo"
    )

    semantic = trace.semantic_result

    assert semantic["status"] == "UNKNOWN"

    assert "economic_object_kind" in semantic["unknowns"]
    assert "intent_action" in semantic["unknowns"]
    assert "intent_side" in semantic["unknowns"]
    assert "market_scope" in semantic["unknowns"]

    values = {
        str(item["value"])
        for item in semantic["facts"]
    }

    assert "UNKNOWN" not in values


def test_trace_relations_are_serialized_deterministically():
    first = _trace(
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    second = _trace(
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    assert (
        first.semantic_result
        == second.semantic_result
    )

    relations = {
        (
            item["subject"],
            item["predicate"],
            item["object"],
        )
        for item in first.semantic_result["relations"]
    }

    assert (
        "QUERY",
        "HAS_SERVICE",
        "FORMATEO_INSTALACION_SO",
    ) in relations

    assert (
        "QUERY",
        "LOCATED_IN",
        "CABA",
    ) in relations


def test_trace_public_decision_contract_is_not_changed_by_semantic_integration():
    raw = (
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    local, remote = cargar_cohortes_pricing_runtime()

    parsed = parse_pricing_query(
        raw,
        language_evidence_type="OBSERVED_USER",
    )

    direct_result = resolver_consulta_pricing(
        raw,
        local_cohortes=local,
        remote_cohortes=remote,
        language_evidence_type="OBSERVED_USER",
        parsed_query=parsed,
    )

    direct_response = asdict(
        presentar_resultado_pricing(
            direct_result
        )
    )

    trace = trace_real_world_query(
        raw,
        local_cohortes=local,
        remote_cohortes=remote,
        source_case_id="block-b-runtime-parity",
        case_origin="OBSERVED_USER",
        input_modality=InputModality.TEXT,
    )

    assert trace.runtime_mutation is False
    assert trace.promotion_authorized is False

    assert trace.readiness == direct_result.status

    assert trace.decision_state == (
        direct_result.decision_label
        or direct_result.status
    )

    assert trace.public_response == direct_response


def test_understanding_trace_uses_new_container_and_semantic_schema_versions():
    trace = _trace(
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    from src.infraestructura.real_world_query_tracer import (
        semantic_trace_payload,
    )

    payload = semantic_trace_payload(
        trace
    )

    assert (
        trace.versions["trace"]
        == "real-world-query-trace-v2"
    )

    assert (
        payload["schema_version"]
        == "real-world-query-trace-semantic-v2"
    )

    assert (
        payload["semantic_result"]["schema_version"]
        == "user-query-understanding-trace-v1"
    )


def test_trace_version_participates_in_replay_fingerprint(
    monkeypatch,
):
    raw = (
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    first = _trace(raw)

    assert (
        first.versions["trace"]
        == "real-world-query-trace-v2"
    )

    assert first.replay_fingerprint.startswith(
        "sha256:"
    )

    from src.infraestructura import (
        real_world_query_tracer,
    )

    monkeypatch.setattr(
        real_world_query_tracer,
        "TRACE_VERSION",
        "real-world-query-trace-v999",
    )

    second = _trace(raw)

    assert (
        second.versions["trace"]
        == "real-world-query-trace-v999"
    )

    assert first.trace_id == second.trace_id

    assert (
        first.replay_fingerprint
        != second.replay_fingerprint
    )


def test_trace_identity_remains_case_identity_not_schema_identity():
    from src.dominio.real_world_query_trace import (
        stable_trace_id,
    )

    raw = (
        "cuanto cobrar por instalacion de windows "
        "a domicilio en caba"
    )

    expected = stable_trace_id(
        source_case_id="block-b-test",
        raw_user_input=raw,
        case_origin="OBSERVED_USER",
    )

    trace = _trace(raw)

    assert trace.trace_id == expected
