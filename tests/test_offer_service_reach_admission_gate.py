from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.build_offer_service_reach_admission_gate import build_artifact
from scripts.build_pricing_statistics import build_runtime_pricing_statistics
from src.api.main import app
from src.aplicacion.pricing_cohort_loader import (
    cargar_cohortes_pricing,
    cargar_cohortes_pricing_runtime,
)
from src.aplicacion.runtime_cohort_lineage_gate import build_runtime_cohort_rows
from src.aplicacion.service_reach_admission_gate import (
    EXCLUSION_REASON_MISSING_SERVICE_REACH,
    EXCLUSION_REASON_SERVICE_REACH_MARKET_MISMATCH,
    GeographicFactKind,
    SERVICE_REACH_GATE_VERSION,
    evaluate_service_reach,
)
from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    EconomicEvidenceDimensionsV2,
    resolve_scalar_dimension,
)
from src.dominio.offer_evidence import EvidenceLineage, OfferReachChargedScopeEvidence
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.infraestructura.economic_dimensions_v2_artifact import (
    load_economic_dimensions_v2_sidecar,
)
from src.infraestructura.real_world_query_tracer import trace_real_world_query


ROOT = Path(__file__).resolve().parents[1]


def test_real_lineage_admissible_observation_cannot_use_provider_location_as_reach():
    local = cargar_cohortes_pricing(
        ROOT / "data/local_pricing_stats_lineage_v1.csv",
        require_runtime_lineage_gate=True,
    )
    cohort = next(item for item in local if "76" in item.observation_ids)
    dimensions = load_economic_dimensions_v2_sidecar(
        ROOT / "data/economic_dimensions_v2.jsonl"
    )["76"]

    assert cohort.market == "Buenos Aires"
    assert cohort.canonical_service == "REPARACION_HARDWARE"
    assert dimensions.location.value.province == "Buenos Aires"
    assert dimensions.geographic_reach.value is None

    decision = evaluate_service_reach(
        observation_id="76",
        provider_location="Buenos Aires",
        runtime_market="Buenos Aires",
        market_scope="LOCAL_SERVICE",
        dimensions=dimensions,
    )

    assert decision.admitted is False
    assert decision.exclusion_reason == EXCLUSION_REASON_MISSING_SERVICE_REACH


def _claim(value: str) -> DimensionClaim[str]:
    return DimensionClaim(
        value=value,
        origin=DimensionOrigin.RAW_SOURCE_OBSERVATION,
        provenance=KnowledgeProvenance("RAW_SOURCE_EXPRESSION", "fixture", "v1"),
        raw_basis=f"explicit {value}",
    )


def _dimensions(
    reach: str | None = None,
    *,
    delivery_mode: str | None = None,
) -> EconomicEvidenceDimensionsV2:
    return EconomicEvidenceDimensionsV2(
        geographic_reach=resolve_scalar_dimension(*((_claim(reach),) if reach else ())),
        delivery_mode=resolve_scalar_dimension(
            *((_claim(delivery_mode),) if delivery_mode else ())
        ),
    )


def _row(observation_id: str, source: str, price: str = "100") -> dict[str, str]:
    return {
        "observation_id": observation_id,
        "source": source,
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "LOCAL_SERVICE",
        "currency": "ARS",
        "canonical_service": "REPARACION_HARDWARE",
        "province": "Córdoba",
        "city": "Córdoba",
        "price_value": price,
        "economic_object_raw": "reparación de hardware",
        "extractor_version": "fixture-v1",
    }


def _lineage(
    root: Path,
    observation_id: str,
    source: str,
    *,
    traceable: bool = True,
) -> OfferReachChargedScopeEvidence:
    if not traceable:
        return OfferReachChargedScopeEvidence(
            observation_id,
            EvidenceLineage(
                observation_id=observation_id,
                source_id=source,
                raw_document_id=None,
                source_url="https://example.test",
                acquired_at=None,
                extractor_version="fixture-v1",
                provenance="fixture",
                linkage_status="UNKNOWN",
                no_linkage_reason="SOURCE_RAW_NOT_AVAILABLE",
            ),
        )
    raw_path = root / "raw" / f"{observation_id}.txt"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(f"raw:{observation_id}", encoding="utf-8")
    digest = hashlib.sha256(raw_path.read_text(encoding="utf-8").encode()).hexdigest()
    return OfferReachChargedScopeEvidence(
        observation_id,
        EvidenceLineage(
            observation_id=observation_id,
            source_id=source,
            raw_document_id=f"sha256:{digest}",
            source_url="https://example.test",
            acquired_at="2026-08-23T00:00:00Z",
            extractor_version="fixture-v1",
            provenance="fixture",
            raw_document_path=raw_path.relative_to(root).as_posix(),
            raw_document_hash=digest,
            linkage_status="TRACEABLE_RAW",
        ),
    )


def test_matching_source_observed_named_area_is_locally_admissible():
    decision = evaluate_service_reach(
        observation_id="fixture-1",
        provider_location="Buenos Aires",
        runtime_market="Córdoba",
        market_scope="LOCAL_SERVICE",
        dimensions=_dimensions("NAMED_AREA:Córdoba"),
    )

    assert decision.admitted is True
    assert decision.reach_kind is GeographicFactKind.NAMED_AREA


def test_provider_location_a_and_reach_b_cannot_admit_market_a():
    decision = evaluate_service_reach(
        observation_id="fixture-1",
        provider_location="Buenos Aires",
        runtime_market="Buenos Aires",
        market_scope="LOCAL_SERVICE",
        dimensions=_dimensions("NAMED_AREA:Córdoba"),
    )

    assert decision.admitted is False
    assert decision.exclusion_reason == EXCLUSION_REASON_SERVICE_REACH_MARKET_MISMATCH


def test_remote_capability_is_not_national_reach_and_unknown_is_preserved():
    dimensions = _dimensions(delivery_mode="REMOTE")
    decision = evaluate_service_reach(
        observation_id="fixture-1",
        provider_location="Buenos Aires",
        runtime_market="AR",
        market_scope="REMOTE_NATIONAL_SERVICE",
        dimensions=dimensions,
    )

    assert dimensions.geographic_reach.value is None
    assert decision.remote_capability is True
    assert decision.service_reach is None
    assert decision.reach_kind is GeographicFactKind.UNKNOWN
    assert decision.admitted is False
    assert decision.exclusion_detail == "REMOTE_CAPABILITY_WITHOUT_NATIONAL_REACH"


def test_only_explicit_national_reach_admits_remote_national_market():
    decision = evaluate_service_reach(
        observation_id="fixture-1",
        provider_location="Buenos Aires",
        runtime_market="AR",
        market_scope="REMOTE_NATIONAL_SERVICE",
        dimensions=_dimensions("NATIONAL", delivery_mode="REMOTE"),
    )

    assert decision.admitted is True
    assert decision.reach_kind is GeographicFactKind.NATIONAL_REACH


def test_lineage_passes_but_reach_fails(tmp_path: Path):
    row = _row("obs-1", "provider-a")
    build = build_runtime_cohort_rows(
        (row,),
        {"obs-1": _lineage(tmp_path, "obs-1", "provider-a")},
        tmp_path,
        market_scope="LOCAL_SERVICE",
        service_reach_dimensions={"obs-1": _dimensions()},
    )

    assert build.decisions[0].admitted is True
    assert build.reach_decisions[0].admitted is False
    assert build.admitted == 0


def test_reach_passes_but_real_observation_234_fails_lineage(tmp_path: Path):
    local, _ = build_runtime_pricing_statistics(
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/offer_evidence_v1.jsonl",
        dimensions_path=ROOT / "data/economic_dimensions_v2.jsonl",
        repository_root=ROOT,
        local_out_path=tmp_path / "local.csv",
        remote_out_path=tmp_path / "remote.csv",
    )
    lineage = {item.observation_id: item for item in local.decisions}["234"]
    reach = {item.observation_id: item for item in local.reach_decisions}["234"]

    assert lineage.admitted is False
    assert reach.admitted is True
    assert reach.service_reach == "NAMED_AREA:Córdoba"
    assert local.admitted == 0


def test_both_gates_pass_and_bad_reach_cannot_inflate_provider_count(tmp_path: Path):
    rows = (
        _row("obs-1", "provider-a", "100"),
        _row("obs-2", "provider-b", "200"),
        _row("obs-3", "provider-c", "1000"),
    )
    evidence = {
        row["observation_id"]: _lineage(
            tmp_path, row["observation_id"], row["source"]
        )
        for row in rows
    }
    dimensions = {
        "obs-1": _dimensions("NAMED_AREA:Córdoba"),
        "obs-2": _dimensions("PROVINCE:Córdoba"),
        "obs-3": _dimensions(),
    }

    build = build_runtime_cohort_rows(
        rows,
        evidence,
        tmp_path,
        market_scope="LOCAL_SERVICE",
        service_reach_dimensions=dimensions,
    )

    assert build.lineage_admitted == 3
    assert build.reach_admitted == 2
    assert build.admitted == 2
    assert build.cohorts[0]["providers_n"] == 2
    assert build.cohorts[0]["median_ars"] == 150.0
    assert build.cohorts[0]["max_ars"] == 200.0


def test_runtime_trace_and_public_api_fail_closed_with_no_admissible_reach():
    local, remote = cargar_cohortes_pricing_runtime()
    query = "Cuánto se cobra por hora por soporte remoto?"
    response = TestClient(app).post("/decision/pricing", json={"query": query})
    trace = trace_real_world_query(
        query,
        local_cohortes=local,
        remote_cohortes=remote,
        source_case_id="service-reach-gate",
        case_origin="CURATED_ENKI",
    )

    assert local == []
    assert remote == []
    assert response.status_code == 200
    assert response.json()["status"] not in {"RANGE_READY", "DECISION_READY"}
    assert response.json()["status"] == "NO_EVIDENCE"
    assert response.json()["evidence"]["observations_n"] == 0
    assert response.json()["evidence"]["providers_n"] == 0
    assert trace.accepted_evidence == ()
    assert trace.readiness == response.json()["status"]


def test_runtime_loader_rejects_lineage_only_artifacts():
    with pytest.raises(ValueError, match=SERVICE_REACH_GATE_VERSION):
        cargar_cohortes_pricing(
            ROOT / "data/local_pricing_stats_lineage_v1.csv",
            require_runtime_lineage_gate=True,
            require_service_reach_gate=True,
        )


def test_offer_service_reach_historical_artifact_is_not_rewritten(tmp_path: Path):
    artifact_path = ROOT / "data/evaluation/offer_service_reach_admission_gate_v1.json"
    historical_bytes = artifact_path.read_bytes()
    generated = build_artifact(
        ROOT,
        tmp_path / "artifact.json",
        local_out_path=tmp_path / "local.csv",
        remote_out_path=tmp_path / "remote.csv",
    )
    assert artifact_path.read_bytes() == historical_bytes
    assert generated["debt_id"] == "TD-002"
    assert generated["observations_before"] == 31
    assert generated["observations_after"] == 0
    assert generated["excluded_missing_service_reach"] == 31
    assert generated["gate_interaction"] == {
        "lineage_pass_reach_fail": 31,
        "reach_pass_lineage_fail": 1,
        "both_pass": 0,
        "both_fail": 52,
    }
    assert generated["trace_engine_parity"]["value"] is True
    assert generated["historical_rows_rewritten"] is False
    assert generated["historical_rows_rewritten"] is False
    assert generated["promotion_authorized"] is False
    assert generated["runtime_learning_writes"] == 0
