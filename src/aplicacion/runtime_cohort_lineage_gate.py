from __future__ import annotations

import hashlib
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from src.aplicacion.provider_independence import (
    PROVIDER_INDEPENDENCE_VERSION,
    stable_provider_id,
)
from src.aplicacion.pricing_dimensions import (
    infer_commercial_context,
    infer_price_scope,
)
from src.aplicacion.service_reach_admission_gate import (
    SERVICE_REACH_GATE_VERSION,
    ServiceReachAdmissionDecision,
    evaluate_service_reach,
)
from src.aplicacion.temporal_evidence_admission_gate import (
    TEMPORAL_GATE_VERSION,
    TemporalAdmissionDecision,
    evaluate_temporal_admission,
)
from src.dominio.economic_evidence import EconomicEvidenceDimensionsV2
from src.dominio.offer_evidence import OfferReachChargedScopeEvidence
from src.dominio.temporal_evidence import TemporalEvidence


LINEAGE_GATE_VERSION = "runtime-cohort-lineage-gate-v1"
EXCLUSION_REASON_MISSING_REPRODUCIBLE_RAW_LINEAGE = (
    "MISSING_REPRODUCIBLE_RAW_LINEAGE"
)


@dataclass(frozen=True)
class RuntimeLineageDecision:
    observation_id: str
    source_id: str
    admitted: bool
    lineage_status: str
    exclusion_reason: str | None
    exclusion_detail: str | None
    raw_document_id: str | None
    raw_document_path: str | None
    raw_document_hash: str | None


@dataclass(frozen=True)
class RuntimeCohortBuild:
    market_scope: str
    cohorts: tuple[dict[str, object], ...]
    decisions: tuple[RuntimeLineageDecision, ...]
    reach_decisions: tuple[ServiceReachAdmissionDecision, ...]
    temporal_decisions: tuple[TemporalAdmissionDecision, ...]
    eligible_before: int
    lineage_admitted: int
    reach_admitted: int
    temporal_admitted: int
    admitted: int
    excluded: int


def _excluded(
    observation_id: str,
    source_id: str,
    detail: str,
    evidence: OfferReachChargedScopeEvidence | None,
) -> RuntimeLineageDecision:
    lineage = evidence.lineage if evidence is not None else None
    status = "UNRESOLVED" if evidence is not None else "MISSING_RAW_LINEAGE"
    return RuntimeLineageDecision(
        observation_id=observation_id,
        source_id=source_id,
        admitted=False,
        lineage_status=status,
        exclusion_reason=EXCLUSION_REASON_MISSING_REPRODUCIBLE_RAW_LINEAGE,
        exclusion_detail=detail,
        raw_document_id=lineage.raw_document_id if lineage else None,
        raw_document_path=lineage.raw_document_path if lineage else None,
        raw_document_hash=lineage.raw_document_hash if lineage else None,
    )


def evaluate_runtime_lineage(
    row: Mapping[str, str],
    evidence: OfferReachChargedScopeEvidence | None,
    repository_root: str | Path,
) -> RuntimeLineageDecision:
    """Admit a constituent only when its RAW identity is reproducible locally."""
    observation_id = row.get("observation_id", "").strip()
    source_id = row.get("source", "").strip()
    if evidence is None:
        return _excluded(observation_id, source_id, "EVIDENCE_RECORD_MISSING", None)

    lineage = evidence.lineage
    if evidence.observation_id != observation_id or lineage.observation_id != observation_id:
        return _excluded(observation_id, source_id, "OBSERVATION_ID_MISMATCH", evidence)
    if lineage.source_id != source_id:
        return _excluded(observation_id, source_id, "SOURCE_ID_MISMATCH", evidence)
    if lineage.linkage_status != "TRACEABLE_RAW":
        return _excluded(
            observation_id,
            source_id,
            lineage.no_linkage_reason or "RAW_LINKAGE_NOT_TRACEABLE",
            evidence,
        )
    if not row.get("extractor_version", "").strip() or not lineage.extractor_version.strip():
        return _excluded(observation_id, source_id, "EXTRACTOR_VERSION_MISSING", evidence)
    if not lineage.provenance.strip():
        return _excluded(observation_id, source_id, "PROVENANCE_MISSING", evidence)
    if not lineage.raw_document_id or not lineage.raw_document_path or not lineage.raw_document_hash:
        return _excluded(observation_id, source_id, "RAW_IDENTITY_INCOMPLETE", evidence)

    root = Path(repository_root).resolve()
    raw_path = (root / lineage.raw_document_path).resolve()
    try:
        raw_path.relative_to(root)
    except ValueError:
        return _excluded(observation_id, source_id, "RAW_PATH_OUTSIDE_REPOSITORY", evidence)
    if not raw_path.is_file():
        return _excluded(observation_id, source_id, "RAW_DOCUMENT_MISSING", evidence)

    try:
        raw_text = raw_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return _excluded(observation_id, source_id, "RAW_DOCUMENT_UNREADABLE", evidence)
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    if digest != lineage.raw_document_hash:
        return _excluded(observation_id, source_id, "RAW_HASH_MISMATCH", evidence)
    if lineage.raw_document_id != f"sha256:{digest}":
        return _excluded(observation_id, source_id, "RAW_DOCUMENT_ID_MISMATCH", evidence)

    return RuntimeLineageDecision(
        observation_id=observation_id,
        source_id=source_id,
        admitted=True,
        lineage_status=(
            "REPRODUCIBLE" if lineage.acquired_at else "HISTORICAL_WITH_LINEAGE"
        ),
        exclusion_reason=None,
        exclusion_detail=None,
        raw_document_id=lineage.raw_document_id,
        raw_document_path=lineage.raw_document_path,
        raw_document_hash=lineage.raw_document_hash,
    )


def _quantile_linear(values: Sequence[float], q: float) -> float:
    xs = sorted(values)
    if not xs:
        raise ValueError("values must not be empty")
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    weight = pos - lo
    return xs[lo] * (1 - weight) + xs[hi] * weight


def _eligible(row: Mapping[str, str], market_scope: str) -> bool:
    if row.get("semantic_role") != "SINGLE_SERVICE":
        return False
    if row.get("market_scope") != market_scope or row.get("currency") != "ARS":
        return False
    if not row.get("canonical_service", "").strip():
        return False
    try:
        float(row.get("price_value", ""))
    except (TypeError, ValueError):
        return False
    return True


def _aggregate(
    rows: Sequence[Mapping[str, str]],
    market_scope: str,
    *,
    service_reach_gated: bool,
    temporal_evidence: Mapping[str, TemporalEvidence] | None,
    provider_dimensions: Mapping[str, EconomicEvidenceDimensionsV2] | None,
) -> list[dict[str, object]]:
    members: dict[tuple[str, str, str, object], list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        market = row["province"] if market_scope == "LOCAL_SERVICE" else "AR"
        key = (
            market,
            row["canonical_service"].strip(),
            infer_price_scope(row.get("economic_object_raw", "")),
            infer_commercial_context(row.get("economic_object_raw", "")),
        )
        members[key].append(row)

    result: list[dict[str, object]] = []
    for (market, service, price_scope, commercial_context), cohort_rows in members.items():
        ordered_rows = sorted(cohort_rows, key=lambda row: row["observation_id"])
        vals = sorted(float(row["price_value"]) for row in ordered_rows)
        sources = {row["source"] for row in ordered_rows}
        provider_ids = {
            provider_id
            for row in ordered_rows
            if (provider_id := stable_provider_id(
                provider_dimensions.get(row["observation_id"])
                if provider_dimensions is not None
                else None
            ))
        }
        n = len(vals)
        source_count = len(sources)
        providers_n = len(provider_ids)
        temporal_members = [
            temporal_evidence[row["observation_id"]]
            for row in ordered_rows
            if temporal_evidence is not None
        ]
        acquired_times = sorted(
            item.acquired_at for item in temporal_members if item.acquired_at
        )
        freshness_versions = sorted(
            {
                item.freshness_policy_version
                for item in temporal_members
                if item.freshness_policy_version
            }
        )
        spread_ratio = max(vals) / min(vals) if min(vals) > 0 else float("inf")
        if n >= 5 and providers_n >= 3 and spread_ratio <= 2.5:
            confidence = "MEDIUM"
        elif n >= 3 and providers_n >= 2 and spread_ratio <= 2.0:
            confidence = "LOW"
        else:
            confidence = "INSUFFICIENT"

        result.append(
            {
                "market": market,
                "canonical_service": service,
                "price_scope": price_scope,
                "commercial_context": commercial_context.value.value,
                "observations_n": n,
                "providers_n": providers_n,
                "source_count": source_count,
                "provider_independence_version": PROVIDER_INDEPENDENCE_VERSION,
                "min_ars": min(vals),
                "q1_ars": _quantile_linear(vals, 0.25),
                "median_ars": statistics.median(vals),
                "q3_ars": _quantile_linear(vals, 0.75),
                "max_ars": max(vals),
                "spread_ratio": round(spread_ratio, 3),
                "evidence_confidence": confidence,
                "decision_ready": "YES" if confidence == "MEDIUM" else "NO",
                "range_ready": "YES" if confidence in {"LOW", "MEDIUM"} else "NO",
                "lineage_gate_version": LINEAGE_GATE_VERSION,
                "service_reach_gate_version": (
                    SERVICE_REACH_GATE_VERSION if service_reach_gated else ""
                ),
                "temporal_gate_version": (
                    TEMPORAL_GATE_VERSION if temporal_evidence is not None else ""
                ),
                "temporal_state": (
                    "CURRENT_REPRODUCIBLE" if temporal_evidence is not None else ""
                ),
                "acquired_at_min": acquired_times[0] if acquired_times else "",
                "acquired_at_max": acquired_times[-1] if acquired_times else "",
                "freshness_policy_version": (
                    freshness_versions[0] if len(freshness_versions) == 1 else ""
                ),
                "observation_ids": "|".join(row["observation_id"] for row in ordered_rows),
            }
        )
    result.sort(key=lambda item: (item["observations_n"], item["providers_n"]), reverse=True)
    return result


def build_runtime_cohort_rows(
    rows: Sequence[Mapping[str, str]],
    evidence_by_observation: Mapping[str, OfferReachChargedScopeEvidence],
    repository_root: str | Path,
    *,
    market_scope: str,
    service_reach_dimensions: Mapping[str, EconomicEvidenceDimensionsV2] | None = None,
    temporal_evidence: Mapping[str, TemporalEvidence] | None = None,
    provider_dimensions: Mapping[str, EconomicEvidenceDimensionsV2] | None = None,
) -> RuntimeCohortBuild:
    """Apply composable lineage/reach admission before runtime aggregation."""
    eligible = [row for row in rows if _eligible(row, market_scope)]
    decisions = tuple(
        evaluate_runtime_lineage(
            row,
            evidence_by_observation.get(row["observation_id"]),
            repository_root,
        )
        for row in eligible
    )
    reach_decisions = tuple(
        evaluate_service_reach(
            observation_id=row["observation_id"],
            provider_location=row.get("province") or None,
            runtime_market=(
                row["province"] if market_scope == "LOCAL_SERVICE" else "AR"
            ),
            market_scope=market_scope,
            dimensions=service_reach_dimensions.get(row["observation_id"]),
        )
        for row in eligible
    ) if service_reach_dimensions is not None else ()
    temporal_decisions = tuple(
        evaluate_temporal_admission(
            observation_id=row["observation_id"],
            evidence=temporal_evidence.get(row["observation_id"]),
        )
        for row in eligible
    ) if temporal_evidence is not None else ()
    lineage_ids = {decision.observation_id for decision in decisions if decision.admitted}
    reach_ids = (
        {decision.observation_id for decision in reach_decisions if decision.admitted}
        if service_reach_dimensions is not None
        else {row["observation_id"] for row in eligible}
    )
    temporal_ids = (
        {
            decision.observation_id
            for decision in temporal_decisions
            if decision.admitted
        }
        if temporal_evidence is not None
        else {row["observation_id"] for row in eligible}
    )
    accepted_ids = lineage_ids & reach_ids & temporal_ids
    accepted = [row for row in eligible if row["observation_id"] in accepted_ids]
    return RuntimeCohortBuild(
        market_scope=market_scope,
        cohorts=tuple(
            _aggregate(
                accepted,
                market_scope,
                service_reach_gated=service_reach_dimensions is not None,
                temporal_evidence=temporal_evidence,
                provider_dimensions=provider_dimensions,
            )
        ),
        decisions=decisions,
        reach_decisions=reach_decisions,
        temporal_decisions=temporal_decisions,
        eligible_before=len(eligible),
        lineage_admitted=len(lineage_ids),
        reach_admitted=len(reach_ids),
        temporal_admitted=len(temporal_ids),
        admitted=len(accepted),
        excluded=len(eligible) - len(accepted),
    )
