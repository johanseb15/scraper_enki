from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.build_temporal_evidence_admissibility import build_artifact
from src.api.main import app
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing_runtime
from src.aplicacion.runtime_cohort_lineage_gate import build_runtime_cohort_rows
from src.aplicacion.service_reach_admission_gate import (
    EXCLUSION_REASON_MISSING_SERVICE_REACH,
)
from src.aplicacion.temporal_evidence_admission_gate import (
    EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE,
    EXCLUSION_REASON_TEMPORAL_CONFLICT,
    EXCLUSION_REASON_TEMPORAL_MISMATCH,
    evaluate_temporal_admission,
)
from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    EconomicEvidenceDimensionsV2,
    resolve_scalar_dimension,
)
from src.dominio.offer_evidence import EvidenceLineage, OfferReachChargedScopeEvidence
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.temporal_evidence import TemporalEvidence, TemporalEvidenceState
from src.infraestructura.real_world_query_tracer import trace_real_world_query
from src.infraestructura.temporal_evidence_artifact import (
    build_temporal_evidence,
    load_temporal_evidence,
)


ROOT = Path(__file__).resolve().parents[1]


def _claim(value: str) -> DimensionClaim[str]:
    return DimensionClaim(
        value=value,
        origin=DimensionOrigin.RAW_SOURCE_OBSERVATION,
        provenance=KnowledgeProvenance("RAW_SOURCE_EXPRESSION", "fixture", "v1"),
        raw_basis=f"explicit {value}",
    )


def _dimensions(reach: str | None) -> EconomicEvidenceDimensionsV2:
    return EconomicEvidenceDimensionsV2(
        geographic_reach=resolve_scalar_dimension(
            *((_claim(reach),) if reach else ())
        )
    )


def _row(observation_id: str = "obs-1") -> dict[str, str]:
    return {
        "observation_id": observation_id,
        "source": "provider-a",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "LOCAL_SERVICE",
        "currency": "ARS",
        "canonical_service": "REPARACION_HARDWARE",
        "province": "Córdoba",
        "city": "Córdoba",
        "price_value": "100",
        "economic_object_raw": "reparación de hardware",
        "extractor_version": "fixture-v1",
    }


def _lineage(root: Path, observation_id: str = "obs-1"):
    raw_path = root / "raw" / f"{observation_id}.txt"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(f"raw:{observation_id}", encoding="utf-8")
    digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    return OfferReachChargedScopeEvidence(
        observation_id,
        EvidenceLineage(
            observation_id=observation_id,
            source_id="provider-a",
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


def _temporal(
    state: TemporalEvidenceState,
    *,
    acquired_at: str | None = "2026-08-23T00:00:00Z",
    current_policy: bool = False,
    filesystem: bool = False,
) -> TemporalEvidence:
    return TemporalEvidence(
        observation_id="obs-1",
        source_id="provider-a",
        extractor_version="fixture-v1",
        raw_document_id="sha256:fixture",
        acquired_at=acquired_at,
        temporal_state=state,
        temporal_identity_known=acquired_at is not None,
        freshness_policy_known=current_policy,
        freshness_policy_version=(
            "controlled-fixture-current-policy-v1" if current_policy else None
        ),
        provenance=("controlled-fixture",),
        filesystem_dates_used_as_evidence=filesystem,
    )


def _brownfield_temporal():
    return build_temporal_evidence(
        ROOT,
        normalization_path=ROOT / "data/semantic_normalization_v4.csv",
        offer_evidence_path=ROOT / "data/offer_evidence_v1.jsonl",
        identities_path=ROOT / "data/offer_evidence_identities_v1.jsonl",
        acquisition_manifest_path=ROOT / "data/targeted_acquisition_manifest_v1.jsonl",
    )


def test_explicit_acquired_at_is_recovered_only_through_reproducible_raw_identity():
    evidence = _brownfield_temporal()["68"]

    assert evidence.acquired_at == "2026-08-22T21:25:53.358653+00:00"
    assert evidence.raw_document_id == (
        "sha256:f043c1c79553ce3df13c9a0984c9287c0d77fa321d2ac7b61393a3d330788b0a"
    )
    assert evidence.source_id == "bairescloud_generic"
    assert evidence.extractor_version == "generic_price_extractor_v3"
    assert evidence.temporal_state is TemporalEvidenceState.HISTORICAL_REPRODUCIBLE
    assert evidence.temporal_identity_known is True
    assert evidence.freshness_policy_known is False


def test_missing_acquired_at_is_not_admissible_for_current_pricing():
    evidence = TemporalEvidence(
        observation_id="76",
        raw_document_id="sha256:fixture",
        temporal_state=TemporalEvidenceState.TEMPORAL_UNKNOWN,
    )

    decision = evaluate_temporal_admission(
        observation_id="76",
        evidence=evidence,
    )

    assert decision.admitted is False
    assert decision.exclusion_reason == EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE


def test_filesystem_mtime_is_never_accepted_as_acquisition_provenance():
    decision = evaluate_temporal_admission(
        observation_id="obs-1",
        evidence=_temporal(
            TemporalEvidenceState.CURRENT_REPRODUCIBLE,
            current_policy=True,
            filesystem=True,
        ),
    )

    assert decision.admitted is False
    assert decision.exclusion_detail == "FILESYSTEM_TIMESTAMP_NOT_ADMISSIBLE"


def test_explicit_historical_observation_is_preserved_not_rewritten_as_current():
    evidence = load_temporal_evidence(ROOT / "data/temporal_evidence_v1.jsonl")["68"]
    decision = evaluate_temporal_admission(observation_id="68", evidence=evidence)

    assert evidence.temporal_state is TemporalEvidenceState.HISTORICAL_REPRODUCIBLE
    assert evidence.acquired_at is not None
    assert decision.admitted is False
    assert decision.exclusion_reason == EXCLUSION_REASON_TEMPORAL_MISMATCH
    assert decision.exclusion_detail == "FRESHNESS_POLICY_UNKNOWN"


def test_real_temporal_unknown_is_excluded_from_current_pricing():
    evidence = _brownfield_temporal()["76"]
    decision = evaluate_temporal_admission(observation_id="76", evidence=evidence)

    assert evidence.temporal_state is TemporalEvidenceState.TEMPORAL_UNKNOWN
    assert evidence.acquired_at is None
    assert evidence.price_validity_time_raw == "febrero 2026"
    assert decision.exclusion_reason == EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE


def test_temporal_conflict_is_preserved_and_excluded():
    evidence = _temporal(TemporalEvidenceState.TEMPORAL_CONFLICT)
    decision = evaluate_temporal_admission(observation_id="obs-1", evidence=evidence)

    assert evidence.temporal_state is TemporalEvidenceState.TEMPORAL_CONFLICT
    assert decision.admitted is False
    assert decision.exclusion_reason == EXCLUSION_REASON_TEMPORAL_CONFLICT


def test_temporal_mismatch_is_excluded():
    decision = evaluate_temporal_admission(
        observation_id="obs-1",
        evidence=_temporal(TemporalEvidenceState.TEMPORAL_MISMATCH),
    )

    assert decision.admitted is False
    assert decision.exclusion_reason == EXCLUSION_REASON_TEMPORAL_MISMATCH


def test_lineage_and_reach_can_pass_while_temporal_fails(tmp_path: Path):
    build = build_runtime_cohort_rows(
        (_row(),),
        {"obs-1": _lineage(tmp_path)},
        tmp_path,
        market_scope="LOCAL_SERVICE",
        service_reach_dimensions={"obs-1": _dimensions("NAMED_AREA:Córdoba")},
        temporal_evidence={
            "obs-1": _temporal(TemporalEvidenceState.TEMPORAL_UNKNOWN, acquired_at=None)
        },
    )

    assert build.decisions[0].admitted is True
    assert build.reach_decisions[0].admitted is True
    assert build.temporal_decisions[0].admitted is False
    assert build.admitted == 0


def test_temporal_can_pass_while_reach_fails(tmp_path: Path):
    build = build_runtime_cohort_rows(
        (_row(),),
        {"obs-1": _lineage(tmp_path)},
        tmp_path,
        market_scope="LOCAL_SERVICE",
        service_reach_dimensions={"obs-1": _dimensions(None)},
        temporal_evidence={
            "obs-1": _temporal(
                TemporalEvidenceState.CURRENT_REPRODUCIBLE,
                current_policy=True,
            )
        },
    )

    assert build.temporal_decisions[0].admitted is True
    assert build.reach_decisions[0].admitted is False
    assert build.reach_decisions[0].exclusion_reason == EXCLUSION_REASON_MISSING_SERVICE_REACH
    assert build.admitted == 0


def test_all_three_gates_pass_only_in_controlled_fixture(tmp_path: Path):
    build = build_runtime_cohort_rows(
        (_row(),),
        {"obs-1": _lineage(tmp_path)},
        tmp_path,
        market_scope="LOCAL_SERVICE",
        service_reach_dimensions={"obs-1": _dimensions("PROVINCE:Córdoba")},
        temporal_evidence={
            "obs-1": _temporal(
                TemporalEvidenceState.CURRENT_REPRODUCIBLE,
                current_policy=True,
            )
        },
    )

    assert build.admitted == 1
    assert build.cohorts[0]["temporal_gate_version"] == (
        "temporal-evidence-admissibility-v1"
    )
    assert build.cohorts[0]["freshness_policy_version"] == (
        "controlled-fixture-current-policy-v1"
    )


def test_temporal_exclusion_reason_survives_runtime_gate_trace(tmp_path: Path):
    build = build_runtime_cohort_rows(
        (_row(),),
        {"obs-1": _lineage(tmp_path)},
        tmp_path,
        market_scope="LOCAL_SERVICE",
        service_reach_dimensions={"obs-1": _dimensions("NAMED_AREA:Córdoba")},
        temporal_evidence={
            "obs-1": _temporal(TemporalEvidenceState.TEMPORAL_UNKNOWN, acquired_at=None)
        },
    )

    decision = build.temporal_decisions[0]
    assert decision.exclusion_reason == EXCLUSION_REASON_MISSING_TEMPORAL_PROVENANCE
    assert decision.exclusion_detail == "ACQUIRED_AT_UNKNOWN"


def test_public_runtime_remains_fail_closed_and_trace_aligned():
    local, remote = cargar_cohortes_pricing_runtime()
    query = "Cuánto se cobra por hora por soporte remoto?"
    response = TestClient(app).post("/decision/pricing", json={"query": query})
    trace = trace_real_world_query(
        query,
        local_cohortes=local,
        remote_cohortes=remote,
        source_case_id="temporal-gate",
        case_origin="CURATED_ENKI",
    )

    assert local == []
    assert remote == []
    assert response.status_code == 200
    assert response.json()["status"] == "NO_EVIDENCE"
    assert trace.readiness == response.json()["status"]
    assert trace.accepted_evidence == ()


def test_temporal_historical_artifact_is_not_rewritten_and_sidecar_is_reproducible(tmp_path: Path):
    artifact_path = ROOT / "data/evaluation/temporal_evidence_admissibility_v1.json"
    historical_bytes = artifact_path.read_bytes()
    generated = build_artifact(
        ROOT,
        tmp_path / "artifact.json",
        temporal_out_path=tmp_path / "temporal.jsonl",
        local_out_path=tmp_path / "local.csv",
        remote_out_path=tmp_path / "remote.csv",
    )
    assert artifact_path.read_bytes() == historical_bytes
    assert generated["historical_rows_rewritten"] is False
    generated_sidecar = [
        json.loads(line)
        for line in (tmp_path / "temporal.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    committed_sidecar = [
        json.loads(line)
        for line in (ROOT / "data/temporal_evidence_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert generated_sidecar == committed_sidecar
    assert generated["acquired_at_known"] == 5
    assert generated["acquired_at_unknown"] == 268
    assert generated["historical_reproducible"] == 5
    assert generated["current_reproducible"] == 0
    assert generated["runtime_admissible"] == 0
    assert generated["runtime_excluded"] == 84
    decisions = {
        item["observation_id"]: item for item in generated["runtime_gate_decisions"]
    }
    assert decisions["68"]["lineage"]["admitted"] is True
    assert decisions["68"]["service_reach"]["reason"] == (
        "MISSING_SERVICE_REACH"
    )
    assert decisions["68"]["temporal"]["reason"] == "TEMPORAL_MISMATCH"
    assert decisions["234"]["lineage"]["reason"] == (
        "MISSING_REPRODUCIBLE_RAW_LINEAGE"
    )
    assert decisions["234"]["service_reach"]["admitted"] is True
    assert generated["filesystem_dates_used_as_evidence"] is False
    assert generated["historical_rows_rewritten"] is False
    assert generated["promotion_authorized"] is False
    assert generated["runtime_learning_writes"] == 0
    assert generated["trace_engine_parity"]["value"] is True
