from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.build_pricing_statistics import build_runtime_pricing_statistics
from scripts.build_runtime_cohort_lineage_gate import build_artifact
from src.api.main import app
from src.aplicacion.pricing_cohort_loader import (
    cargar_cohortes_pricing,
    cargar_cohortes_pricing_runtime,
)
from src.aplicacion.runtime_cohort_lineage_gate import (
    EXCLUSION_REASON_MISSING_REPRODUCIBLE_RAW_LINEAGE,
    build_runtime_cohort_rows,
)
from src.dominio.offer_evidence import EvidenceLineage, OfferReachChargedScopeEvidence
from src.infraestructura.real_world_query_tracer import trace_real_world_query


ROOT = Path(__file__).resolve().parents[1]


def _semantic_row(observation_id: str, source: str, price: str) -> dict[str, str]:
    return {
        "observation_id": observation_id,
        "source": source,
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "currency": "ARS",
        "canonical_service": "soporte informatico remoto",
        "province": "",
        "price_value": price,
        "economic_object_raw": "soporte por hora",
        "source_type": "PUBLIC_WEB",
        "extractor_version": "fixture-extractor-v1",
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
            observation_id=observation_id,
            lineage=EvidenceLineage(
                observation_id=observation_id,
                source_id=source,
                raw_document_id=None,
                source_url="https://example.test/offer",
                acquired_at=None,
                extractor_version="fixture-extractor-v1",
                provenance="fixture",
                linkage_status="UNKNOWN",
                no_linkage_reason="SOURCE_RAW_NOT_AVAILABLE",
            ),
            claims=(),
        )

    raw_path = root / "data" / "raw" / f"{observation_id}.txt"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(f"raw:{observation_id}", encoding="utf-8")
    digest = hashlib.sha256(raw_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    relative_path = raw_path.relative_to(root).as_posix()
    return OfferReachChargedScopeEvidence(
        observation_id=observation_id,
        lineage=EvidenceLineage(
            observation_id=observation_id,
            source_id=source,
            raw_document_id=f"sha256:{digest}",
            source_url="https://example.test/offer",
            acquired_at="2026-08-23T00:00:00Z",
            extractor_version="fixture-extractor-v1",
            provenance="fixture",
            raw_document_path=relative_path,
            raw_document_hash=digest,
            linkage_status="TRACEABLE_RAW",
        ),
        claims=(),
    )


def test_fully_reproducible_constituent_is_admitted(tmp_path: Path) -> None:
    row = _semantic_row("obs-1", "provider-a", "100")
    evidence = {"obs-1": _lineage(tmp_path, "obs-1", "provider-a")}

    build = build_runtime_cohort_rows(
        (row,), evidence, tmp_path, market_scope="REMOTE_NATIONAL_SERVICE"
    )

    assert build.eligible_before == 1
    assert build.admitted == 1
    assert build.excluded == 0
    assert build.decisions[0].lineage_status == "REPRODUCIBLE"
    assert build.cohorts[0]["observation_ids"] == "obs-1"


def test_missing_raw_and_url_only_constituents_are_excluded(tmp_path: Path) -> None:
    rows = (
        _semantic_row("obs-missing", "provider-a", "100"),
        _semantic_row("obs-url", "provider-b", "200"),
    )
    evidence = {"obs-url": _lineage(tmp_path, "obs-url", "provider-b", traceable=False)}

    build = build_runtime_cohort_rows(
        rows, evidence, tmp_path, market_scope="REMOTE_NATIONAL_SERVICE"
    )

    assert build.admitted == 0
    assert build.excluded == 2
    assert not build.cohorts
    assert {decision.exclusion_reason for decision in build.decisions} == {
        EXCLUSION_REASON_MISSING_REPRODUCIBLE_RAW_LINEAGE
    }


def test_invalid_constituent_cannot_inflate_providers_or_statistics(tmp_path: Path) -> None:
    rows = (
        _semantic_row("obs-1", "provider-a", "100"),
        _semantic_row("obs-2", "provider-b", "1000"),
        _semantic_row("obs-3", "provider-c", "200"),
    )
    evidence = {
        "obs-1": _lineage(tmp_path, "obs-1", "provider-a"),
        "obs-2": _lineage(tmp_path, "obs-2", "provider-b", traceable=False),
        "obs-3": _lineage(tmp_path, "obs-3", "provider-c"),
    }

    build = build_runtime_cohort_rows(
        rows, evidence, tmp_path, market_scope="REMOTE_NATIONAL_SERVICE"
    )

    assert build.admitted == 2
    assert build.excluded == 1
    cohort = build.cohorts[0]
    assert cohort["observations_n"] == 2
    assert cohort["providers_n"] == 2
    assert cohort["median_ars"] == 150.0
    assert cohort["min_ars"] == 100.0
    assert cohort["max_ars"] == 200.0
    assert cohort["observation_ids"] == "obs-1|obs-3"


def test_source_identity_mismatch_is_unresolved_and_excluded(tmp_path: Path) -> None:
    row = _semantic_row("obs-1", "provider-a", "100")
    evidence = {"obs-1": _lineage(tmp_path, "obs-1", "provider-b")}

    build = build_runtime_cohort_rows(
        (row,), evidence, tmp_path, market_scope="REMOTE_NATIONAL_SERVICE"
    )

    assert build.admitted == 0
    assert build.decisions[0].lineage_status == "UNRESOLVED"
    assert build.decisions[0].exclusion_detail == "SOURCE_ID_MISMATCH"


def test_historical_constituent_with_reproducible_lineage_is_admitted(tmp_path: Path) -> None:
    row = _semantic_row("obs-1", "provider-a", "100")
    record = _lineage(tmp_path, "obs-1", "provider-a")
    historical = replace(record, lineage=replace(record.lineage, acquired_at=None))

    build = build_runtime_cohort_rows(
        (row,),
        {"obs-1": historical},
        tmp_path,
        market_scope="REMOTE_NATIONAL_SERVICE",
    )

    assert build.admitted == 1
    assert build.decisions[0].lineage_status == "HISTORICAL_WITH_LINEAGE"


def test_raw_hash_mismatch_is_fail_closed(tmp_path: Path) -> None:
    row = _semantic_row("obs-1", "provider-a", "100")
    record = _lineage(tmp_path, "obs-1", "provider-a")
    (tmp_path / record.lineage.raw_document_path).write_text("mutated", encoding="utf-8")

    build = build_runtime_cohort_rows(
        (row,),
        {"obs-1": record},
        tmp_path,
        market_scope="REMOTE_NATIONAL_SERVICE",
    )

    assert build.admitted == 0
    assert build.decisions[0].exclusion_detail == "RAW_HASH_MISMATCH"


def test_runtime_loader_rejects_legacy_ungated_aggregate() -> None:
    with pytest.raises(ValueError, match="runtime-cohort-lineage-gate-v1"):
        cargar_cohortes_pricing(
            ROOT / "data/remote_pricing_stats_v2.csv",
            require_runtime_lineage_gate=True,
        )


def test_real_p0_cohort_is_rebuilt_without_mutating_historical_inputs(tmp_path: Path) -> None:
    normalization = ROOT / "data/semantic_normalization_v4.csv"
    evidence_path = ROOT / "data/offer_evidence_v1.jsonl"
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (normalization, evidence_path)
    }
    _, remote = build_runtime_pricing_statistics(
        normalization,
        evidence_path,
        repository_root=ROOT,
        local_out_path=tmp_path / "local.csv",
        remote_out_path=tmp_path / "remote.csv",
    )

    cohort = next(
        item
        for item in remote.cohorts
        if item["canonical_service"] == "SOPORTE_REMOTO"
        and item["price_scope"] == "PER_HOUR"
        and item["commercial_context"] == "STANDARD"
    )
    decisions = {item.observation_id: item for item in remote.decisions}
    assert cohort["observation_ids"] == "68"
    assert cohort["observations_n"] == 1
    assert decisions["68"].admitted is True
    assert decisions["147"].admitted is False
    assert decisions["213"].admitted is False
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before} == before


def test_runtime_api_and_trace_only_project_gated_cohort_members() -> None:
    local, remote = cargar_cohortes_pricing_runtime()
    query = "Cuánto se está cobrando por hora por soporte remoto?"
    response = TestClient(app).post("/decision/pricing", json={"query": query})
    trace = trace_real_world_query(
        query,
        local_cohortes=local,
        remote_cohortes=remote,
        source_case_id="runtime-lineage-gate-contract",
        case_origin="CURATED_ENKI",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "INSUFFICIENT_EVIDENCE"
    assert response.json()["evidence"]["observation_ids"] == ["68"]
    assert trace.readiness == response.json()["status"]
    assert trace.accepted_evidence == (
        "pricing-cohort:AR:SOPORTE_REMOTO:PER_HOUR:STANDARD",
    )
    accepted = next(item for item in remote if item.evidence_id in trace.accepted_evidence)
    assert accepted.observation_ids == ("68",)


def test_lineage_gate_artifact_is_reproducible_and_records_no_semantic_drift(
    tmp_path: Path,
) -> None:
    generated = build_artifact(
        ROOT,
        tmp_path / "runtime_cohort_lineage_gate_v1.json",
        local_out_path=tmp_path / "local.csv",
        remote_out_path=tmp_path / "remote.csv",
    )
    committed = json.loads(
        (ROOT / "data/evaluation/runtime_cohort_lineage_gate_v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert generated == committed
    assert generated["runtime_admitted_before"] == 84
    assert generated["runtime_admitted_after"] == 31
    assert generated["excluded_missing_lineage"] == 53
    assert generated["trace_engine_parity"]["value"] is True
    assert generated["unexpected_semantic_drift"] == 0
    assert generated["historical_rows_rewritten"] is False
