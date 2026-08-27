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
from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    DimensionValue,
    EconomicEvidenceDimensionsV2,
    ProviderIdentity,
)
from src.dominio.offer_evidence import EvidenceLineage, OfferReachChargedScopeEvidence
from src.dominio.semantic_knowledge import KnowledgeProvenance
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
    assert cohort["source_count"] == 2
    assert cohort["providers_n"] == 0
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
            and item["commercial_context"] == "UNKNOWN"
    )
    decisions = {item.observation_id: item for item in remote.decisions}
    assert cohort["observation_ids"] == "68"
    assert cohort["observations_n"] == 1
    assert decisions["68"].admitted is True
    assert decisions["147"].admitted is False
    assert decisions["213"].admitted is False
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before} == before


def test_runtime_api_and_trace_do_not_reintroduce_lineage_only_members() -> None:
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
    assert response.json()["status"] == "NO_EVIDENCE"
    assert response.json()["evidence"]["observation_ids"] == []
    assert trace.readiness == response.json()["status"]
    assert trace.accepted_evidence == ()
    assert remote == []


def test_lineage_gate_historical_artifact_is_not_rewritten(
    tmp_path: Path,
) -> None:
    artifact_path = ROOT / "data/evaluation/runtime_cohort_lineage_gate_v1.json"
    historical_bytes = artifact_path.read_bytes()
    generated = build_artifact(
        ROOT,
        tmp_path / "runtime_cohort_lineage_gate_v1.json",
        local_out_path=tmp_path / "local.csv",
        remote_out_path=tmp_path / "remote.csv",
    )
    assert artifact_path.read_bytes() == historical_bytes
    assert generated["runtime_admitted_before"] == 84
    assert generated["runtime_admitted_after"] == 31
    assert generated["excluded_missing_lineage"] == 53
    assert generated["trace_engine_parity"]["value"] is True
    assert generated["historical_rows_rewritten"] is False


def _provider_dimensions(provider_id: str | None, *, source="source"):
    if provider_id is None:
        return EconomicEvidenceDimensionsV2()
    name = provider_id.rsplit(":", 1)[-1]
    provider = ProviderIdentity(
        provider_id=provider_id,
        provider_name=name,
        source=source,
    )
    return EconomicEvidenceDimensionsV2(
        provider_identity=DimensionValue(
            value=provider,
            status=DimensionStatus.INFERRED,
            claims=(
                DimensionClaim(
                    value=provider,
                    origin=DimensionOrigin.REGISTRY_CLAIM,
                    provenance=KnowledgeProvenance(
                        "PROVIDER_SOURCE_REGISTRY",
                        f"source={source};provider={name}",
                        "pricing-source-registry-v1",
                    ),
                    raw_basis=f"registry source={source!r} provider={name!r}",
                ),
            ),
        ),
    )


def _conflicted_provider_dimensions():
    first = ProviderIdentity("provider:x:1", "Provider X", "source-a")
    second = ProviderIdentity("provider:y:2", "Provider Y", "source-a")
    return EconomicEvidenceDimensionsV2(
        provider_identity=DimensionValue(
            value=None,
            status=DimensionStatus.CONFLICTED,
            claims=(
                DimensionClaim(
                    value=first,
                    origin=DimensionOrigin.REGISTRY_CLAIM,
                    provenance=KnowledgeProvenance(
                        "PROVIDER_SOURCE_REGISTRY",
                        "source=source-a;provider=Provider X",
                        "pricing-source-registry-v1",
                    ),
                    raw_basis="registry source='source-a' provider='Provider X'",
                ),
                DimensionClaim(
                    value=second,
                    origin=DimensionOrigin.NORMALIZED_FIELD,
                    provenance=KnowledgeProvenance(
                        "SEMANTIC_NORMALIZATION_FIELD",
                        "source=source-a;provider=Provider Y",
                        "semantic-normalization-v4",
                    ),
                    raw_basis="normalized provider='Provider Y'",
                ),
            ),
        ),
    )


def test_same_provider_multi_source_counts_one_independent_provider(tmp_path: Path) -> None:
    rows = (
        _semantic_row("obs-1", "source-a", "100"),
        _semantic_row("obs-2", "source-b", "120"),
    )
    evidence = {
        "obs-1": _lineage(tmp_path, "obs-1", "source-a"),
        "obs-2": _lineage(tmp_path, "obs-2", "source-b"),
    }
    dimensions = {
        "obs-1": _provider_dimensions("provider:shared:abc", source="source-a"),
        "obs-2": _provider_dimensions("provider:shared:abc", source="source-b"),
    }

    build = build_runtime_cohort_rows(
        rows,
        evidence,
        tmp_path,
        market_scope="REMOTE_NATIONAL_SERVICE",
        provider_dimensions=dimensions,
    )

    cohort = build.cohorts[0]
    assert cohort["observations_n"] == 2
    assert cohort["source_count"] == 2
    assert cohort["providers_n"] == 1
    assert cohort["evidence_confidence"] == "INSUFFICIENT"
    assert cohort["range_ready"] == "NO"


def test_different_providers_count_as_independent(tmp_path: Path) -> None:
    rows = (
        _semantic_row("obs-1", "source-a", "100"),
        _semantic_row("obs-2", "source-b", "120"),
        _semantic_row("obs-3", "source-c", "130"),
    )
    evidence = {
        "obs-1": _lineage(tmp_path, "obs-1", "source-a"),
        "obs-2": _lineage(tmp_path, "obs-2", "source-b"),
        "obs-3": _lineage(tmp_path, "obs-3", "source-c"),
    }
    dimensions = {
        "obs-1": _provider_dimensions("provider:a:1", source="source-a"),
        "obs-2": _provider_dimensions("provider:b:2", source="source-b"),
        "obs-3": _provider_dimensions("provider:c:3", source="source-c"),
    }

    build = build_runtime_cohort_rows(
        rows,
        evidence,
        tmp_path,
        market_scope="REMOTE_NATIONAL_SERVICE",
        provider_dimensions=dimensions,
    )

    cohort = build.cohorts[0]
    assert cohort["observations_n"] == 3
    assert cohort["source_count"] == 3
    assert cohort["providers_n"] == 3
    assert cohort["range_ready"] == "YES"


def test_same_provider_multi_snapshot_counts_one_independent_provider(tmp_path: Path) -> None:
    rows = (
        _semantic_row("obs-1", "source-a", "100"),
        _semantic_row("obs-2", "source-a", "120"),
        _semantic_row("obs-3", "source-a", "130"),
    )
    evidence = {
        "obs-1": _lineage(tmp_path, "obs-1", "source-a"),
        "obs-2": _lineage(tmp_path, "obs-2", "source-a"),
        "obs-3": _lineage(tmp_path, "obs-3", "source-a"),
    }
    dimensions = {
        observation_id: _provider_dimensions("provider:a:1", source="source-a")
        for observation_id in ("obs-1", "obs-2", "obs-3")
    }

    build = build_runtime_cohort_rows(
        rows,
        evidence,
        tmp_path,
        market_scope="REMOTE_NATIONAL_SERVICE",
        provider_dimensions=dimensions,
    )

    cohort = build.cohorts[0]
    assert cohort["observations_n"] == 3
    assert cohort["source_count"] == 1
    assert cohort["providers_n"] == 1
    assert cohort["range_ready"] == "NO"


def test_unknown_or_conflicted_provider_identity_does_not_invent_independence(tmp_path: Path) -> None:
    rows = (
        _semantic_row("obs-1", "source-a", "100"),
        _semantic_row("obs-2", "source-b", "120"),
    )
    evidence = {
        "obs-1": _lineage(tmp_path, "obs-1", "source-a"),
        "obs-2": _lineage(tmp_path, "obs-2", "source-b"),
    }
    dimensions = {
        "obs-1": _provider_dimensions(None),
        "obs-2": _conflicted_provider_dimensions(),
    }

    build = build_runtime_cohort_rows(
        rows,
        evidence,
        tmp_path,
        market_scope="REMOTE_NATIONAL_SERVICE",
        provider_dimensions=dimensions,
    )

    cohort = build.cohorts[0]
    assert cohort["observations_n"] == 2
    assert cohort["source_count"] == 2
    assert cohort["providers_n"] == 0
    assert cohort["range_ready"] == "NO"


def test_runtime_loader_requires_provider_independence_contract(tmp_path: Path) -> None:
    path = tmp_path / "legacy_runtime.csv"
    path.write_text(
        "market,canonical_service,observations_n,providers_n,min_ars,q1_ars,median_ars,q3_ars,max_ars,spread_ratio,evidence_confidence,decision_ready,range_ready,lineage_gate_version,observation_ids\n"
        "AR,SOPORTE_REMOTO,3,3,100,110,120,130,140,1.4,LOW,NO,YES,runtime-cohort-lineage-gate-v1,obs-1|obs-2|obs-3\n",
        encoding="utf-8-sig",
    )

    with pytest.raises(ValueError, match="provider-independence-contract-v1"):
        cargar_cohortes_pricing(
            path,
            require_runtime_lineage_gate=True,
            require_provider_independence=True,
        )
