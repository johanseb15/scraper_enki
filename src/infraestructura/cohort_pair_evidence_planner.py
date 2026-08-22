from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from itertools import combinations
from pathlib import Path
from typing import Any

from src.dominio.economic_evidence_pair import (
    EconomicEvidencePair,
    MinimalPairUnlockSet,
    PairClaimRequirement,
    PairCompatibilityState,
)
from src.infraestructura.economic_dimensions_loader import (
    load_versioned_economic_dimensions_sidecar,
)
from src.infraestructura.offer_evidence_artifact import load_offer_evidence_sidecar
from src.infraestructura.semantic_understanding_batch import compose_semantic_understanding_rows


SCHEMA_VERSION = "cohort-pair-evidence-planner-v1"
DEFAULT_COHORT = "VISITA_TECNICA_DOMICILIO"
REQUIRED_DIMENSIONS = (
    "price_scope",
    "delivery_mode",
    "geographic_reach",
    "commercial_context",
    "device_scope",
    "hardware_included",
    "materials_included",
)
EXPLICIT_MISMATCH_NAMES = {
    "price_scope": "PRICE_SCOPE_MISMATCH",
    "delivery_mode": "DELIVERY_MODE_MISMATCH",
    "geographic_reach": "GEOGRAPHIC_REACH_MISMATCH",
    "commercial_context": "COMMERCIAL_CONTEXT_MISMATCH",
    "device_scope": "DEVICE_SCOPE_MISMATCH",
    "hardware_included": "HARDWARE_INCLUDED_MISMATCH",
    "materials_included": "MATERIALS_INCLUDED_MISMATCH",
}


def build_cohort_pair_evidence_plan(
    normalization_path: str | Path,
    registry_path: str | Path,
    dimensions_path: str | Path,
    offer_evidence_path: str | Path,
    identities_path: str | Path,
    acquisition_manifest_path: str | Path,
    audit_path: str | Path,
    pairs_path: str | Path,
    unlock_sets_path: str | Path,
    counterfactuals_path: str | Path,
    plan_path: str | Path,
    summary_path: str | Path,
    *,
    cohort: str = DEFAULT_COHORT,
) -> dict[str, Any]:
    rows = _csv(normalization_path)
    cohort_rows = [row for row in rows if row["canonical_service"] == cohort]
    registry = {row["source"]: row for row in _csv(registry_path)}
    dimensions = load_versioned_economic_dimensions_sidecar(dimensions_path)
    evidence = load_offer_evidence_sidecar(offer_evidence_path)
    identities = {item["observation_id"]: item for item in _jsonl(identities_path)}
    acquisitions = {item["source"]: item for item in _jsonl(acquisition_manifest_path)}
    envelopes = compose_semantic_understanding_rows(
        cohort_rows,
        interpretation_reference=str(normalization_path),
        interpretation_version=SCHEMA_VERSION,
    )
    semantic_status = {
        envelope.observation.observation_id: envelope.status.value for envelope in envelopes
    }
    source_counts = Counter(row["source"] for row in cohort_rows)
    audits = [
        _audit_row(
            row,
            registry[row["source"]],
            dimensions[row["observation_id"]],
            evidence.get(row["observation_id"]),
            identities.get(row["observation_id"]),
            acquisitions.get(row["source"]),
            semantic_status[row["observation_id"]],
        )
        for row in cohort_rows
    ]
    audits.sort(key=lambda item: int(item["observation_id"]))
    by_id = {item["observation_id"]: item for item in audits}

    pairs: list[EconomicEvidencePair] = []
    unlock_sets: list[MinimalPairUnlockSet] = []
    counterfactuals: list[dict[str, Any]] = []
    for left, right in combinations(audits, 2):
        pair, unlock = evaluate_pair(left, right, source_counts=source_counts)
        pairs.append(pair)
        unlock_sets.append(unlock)
        counterfactuals.extend(build_pair_counterfactuals(pair))

    ranked = sorted(
        pairs,
        key=lambda item: (
            item.compatibility_state is not PairCompatibilityState.MISSING_EVIDENCE,
            len(item.missing_evidence),
            -item.score,
            item.pair_id,
        ),
    )
    pair_rank = {item.pair_id: rank for rank, item in enumerate(ranked, 1)}
    pair_rows = [_pair_payload(item, pair_rank[item.pair_id]) for item in pairs]
    unlock_rows = [_unlock_payload(item) for item in unlock_sets]
    plan = _build_actions(audits, pairs, registry, source_counts)

    current_pairs = [item for item in pairs if item.compatibility_state is PairCompatibilityState.COMPARABLE]
    potential_pairs = [
        item for item in pairs
        if item.compatibility_state in {
            PairCompatibilityState.COMPARABLE,
            PairCompatibilityState.MISSING_EVIDENCE,
        }
    ]
    routes = _cohort_routes(potential_pairs, by_id)
    current_readiness = _cohort_readiness(current_pairs, by_id)
    max_readiness = (
        "READY" if routes["READY"] else
        "PARTIAL" if routes["PARTIAL"] else
        _cohort_readiness(potential_pairs, by_id)
    )
    metrics = _metrics(audits, pairs, plan)
    cohort_metrics = {
        "OBSERVATIONS": len(audits),
        "PROVIDERS": len({item["provider_id"] for item in audits}),
        "PAIRS": len(pairs),
        "COMPARABLE_PAIRS": len(current_pairs),
        "POTENTIALLY_UNLOCKABLE_PAIRS": sum(
            item.compatibility_state is PairCompatibilityState.MISSING_EVIDENCE for item in pairs
        ),
        "CURRENT_PROVIDER_COVERAGE": _provider_coverage(current_pairs),
        "MAX_PROVIDER_COVERAGE_IF_TOP_ACTIONS_SUCCEED": _provider_coverage(potential_pairs),
        "CURRENT_READINESS": current_readiness,
        "MAX_COUNTERFACTUAL_READINESS": max_readiness,
    }
    cohort_score_breakdown = {
        "OBSERVATIONS": len(audits),
        "INDEPENDENT_PROVIDERS": 2 * len({item["provider_id"] for item in audits}),
        "POTENTIALLY_UNLOCKABLE_PAIRS": len(potential_pairs),
        "PARTIAL_ROUTE": 10 if routes["PARTIAL"] else 0,
        "READY_ROUTE": 15 if routes["READY"] else 0,
        "NO_CURRENT_COMPARABLE_PENALTY": -8 if not current_pairs else 0,
        "MINIMUM_ROUTE_SIZE_PENALTY": -min(12, routes["FIRST_PAIR"]["claim_count"] if routes["FIRST_PAIR"] else 12),
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "cohort": cohort,
        "pair_metrics": metrics,
        "cohort_metrics": cohort_metrics,
        "routes": routes,
        "cohort_ranking": [{
            "rank": 1,
            "cohort": cohort,
            "score": sum(cohort_score_breakdown.values()),
            "score_breakdown": cohort_score_breakdown,
        }],
        "planned_actions": len(plan),
        "positive_value_actions": sum(item["expected_pairs_unlocked"] > 0 for item in plan),
        "zero_value_actions": sum(item["expected_pairs_unlocked"] == 0 for item in plan),
    }
    _write_jsonl(audit_path, audits)
    _write_jsonl(pairs_path, pair_rows)
    _write_jsonl(unlock_sets_path, unlock_rows)
    _write_jsonl(counterfactuals_path, counterfactuals)
    _write_jsonl(plan_path, plan)
    Path(summary_path).write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def evaluate_pair(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    source_counts: Counter[str] | None = None,
) -> tuple[EconomicEvidencePair, MinimalPairUnlockSet]:
    if int(left["observation_id"]) > int(right["observation_id"]):
        left, right = right, left
    pair_id = f"pair:{left['observation_id']}:{right['observation_id']}"
    hard: list[str] = []
    explicit: list[str] = []
    missing: list[PairClaimRequirement] = []
    if left["canonical_service"] != right["canonical_service"]:
        hard.append("CANONICAL_MISMATCH")
    if left["provider_id"] == right["provider_id"]:
        hard.append("SAME_PROVIDER_NOT_INDEPENDENT")
    if left["semantic_role"] == "HARDWARE_PRODUCT" or right["semantic_role"] == "HARDWARE_PRODUCT":
        hard.append("HARDWARE_SERVICE_BOUNDARY")
    if left["semantic_status"] in {"AMBIGUOUS", "UNKNOWN", "UNREPRESENTED"} or right["semantic_status"] in {"AMBIGUOUS", "UNKNOWN", "UNREPRESENTED"}:
        hard.append("SEMANTIC_AMBIGUITY_INCOMPATIBLE")
    if left["temporal_status"] == "TEMPORAL_MISMATCH" or right["temporal_status"] == "TEMPORAL_MISMATCH":
        hard.append("TEMPORAL_MISMATCH")

    _hard_dimension(left, right, "currency", "CURRENCY", hard, missing)
    _hard_dimension(left, right, "bundle_status", "BUNDLE", hard, missing)
    if _usable(left, "bundle_status") and left["dimensions"]["bundle_status"]["value"] == "COMPOSITE":
        hard.append("BUNDLE_INCOMPATIBILITY")
    if _usable(right, "bundle_status") and right["dimensions"]["bundle_status"]["value"] == "COMPOSITE":
        hard.append("BUNDLE_INCOMPATIBILITY")

    for name in REQUIRED_DIMENSIONS:
        left_known, right_known = _usable(left, name), _usable(right, name)
        if not left_known:
            missing.append(PairClaimRequirement(left["observation_id"], "A", name))
        if not right_known:
            missing.append(PairClaimRequirement(right["observation_id"], "B", name))
        if left_known and right_known and not _compatible(
            left["dimensions"][name]["value"], right["dimensions"][name]["value"]
        ):
            explicit.append(EXPLICIT_MISMATCH_NAMES[name])

    hard_tuple = tuple(sorted(set(hard)))
    explicit_tuple = tuple(sorted(set(explicit)))
    missing_tuple = tuple(sorted(set(missing)))
    if hard_tuple:
        state = PairCompatibilityState.HARD_BLOCKED
    elif explicit_tuple:
        state = PairCompatibilityState.EXPLICIT_MISMATCH
    elif missing_tuple:
        state = PairCompatibilityState.MISSING_EVIDENCE
    else:
        state = PairCompatibilityState.COMPARABLE
    score, breakdown = _pair_score(left, right, hard_tuple, explicit_tuple, missing_tuple, source_counts or Counter())
    pair = EconomicEvidencePair(
        pair_id=pair_id,
        observation_a=left["observation_id"],
        observation_b=right["observation_id"],
        canonical=left["canonical_service"],
        provider_a=left["provider_id"],
        provider_b=right["provider_id"],
        hard_blockers=hard_tuple,
        missing_evidence=missing_tuple,
        explicit_mismatches=explicit_tuple,
        compatibility_state=state,
        temporal_compatibility=_pair_temporal(left, right),
        score=score,
        score_breakdown=tuple(breakdown.items()),
        provenance=(left["provenance"], right["provenance"]),
    )
    could = state is PairCompatibilityState.MISSING_EVIDENCE or state is PairCompatibilityState.COMPARABLE
    unlock = MinimalPairUnlockSet(
        pair_id=pair_id,
        required_claims=missing_tuple,
        hard_blockers=hard_tuple,
        explicit_mismatches=explicit_tuple,
        unresolved_after_hypothetical_success=tuple([*hard_tuple, *explicit_tuple]),
        could_be_comparable=could,
        could_contribute_to_partial=could,
        could_contribute_to_ready=could,
    )
    return pair, unlock


def build_pair_counterfactuals(pair: EconomicEvidencePair) -> list[dict[str, Any]]:
    claims = tuple(item.claim_id for item in pair.missing_evidence)
    rows = []
    steps = range(1, len(claims) + 1) if claims else (0,)
    for step in steps:
        applied = claims[:step]
        remaining = claims[step:]
        potential = not pair.hard_blockers and not pair.explicit_mismatches and not remaining
        rows.append({
            "schema_version": "pair-set-counterfactual-v1",
            "pair_id": pair.pair_id,
            "step": step,
            "assumed_compatible_claims": list(applied),
            "remaining_missing_claims": list(remaining),
            "hard_blockers": list(pair.hard_blockers),
            "explicit_mismatches": list(pair.explicit_mismatches),
            "potentially_comparable": potential,
            "explanation": (
                "Upper bound only: assumed claims become known and compatible; no values invented."
            ),
        })
    return rows


def _audit_row(row, registry, dimensions, evidence, identity, acquisition, semantic_status):
    values = dimensions.all_dimensions()
    if identity and identity["status"] == "RESOLVED" and acquisition:
        temporal_status = "CURRENT_EXACT_OFFER"
        temporal_version = f"{acquisition['acquired_at']}@sha256:{acquisition['content_hash']}"
        provenance = identity["raw_document_id"]
    elif identity and identity["status"] != "RESOLVED":
        temporal_status = "TEMPORAL_MISMATCH"
        temporal_version = identity["reason"]
        provenance = identity.get("raw_document_id") or "UNRESOLVED"
    elif evidence and evidence.lineage.linkage_status == "TRACEABLE_RAW":
        temporal_status = "HISTORICAL_TRACEABLE"
        temporal_version = evidence.lineage.raw_document_id or "HISTORICAL_UNDATED"
        provenance = evidence.lineage.provenance or "offer-evidence-v1"
    else:
        temporal_status = "UNVERSIONED"
        temporal_version = "NORMALIZED_LEGACY_WITHOUT_RAW_LINKAGE"
        provenance = "semantic_normalization_v4.csv"
    return {
        "schema_version": "economic-evidence-cohort-audit-v1",
        "observation_id": row["observation_id"],
        "raw_economic_expression": row["economic_object_raw"],
        "canonical_service": row["canonical_service"],
        "semantic_role": row["semantic_role"],
        "semantic_status": semantic_status,
        "provider_id": _json_value(values["provider_identity"].value).get("provider_id"),
        "provider_name": registry["provider"],
        "source": row["source"],
        "source_url": registry["url"],
        "price": row["price_value"],
        "currency": row["currency"],
        "dimensions": {name: _dimension_payload(value) for name, value in values.items()},
        "raw_lineage": evidence.lineage.linkage_status if evidence else "UNKNOWN",
        "raw_document": evidence.lineage.raw_document_path if evidence else None,
        "temporal_status": temporal_status,
        "temporal_version": temporal_version,
        "provenance": provenance,
    }


def _hard_dimension(left, right, name, label, hard, missing):
    a, b = _usable(left, name), _usable(right, name)
    if not a:
        missing.append(PairClaimRequirement(left["observation_id"], "A", name))
    if not b:
        missing.append(PairClaimRequirement(right["observation_id"], "B", name))
    left_status = left["dimensions"][name]["status"]
    right_status = right["dimensions"][name]["status"]
    if "CONFLICT" in left_status or "CONFLICT" in right_status:
        hard.append(f"{label}_CONFLICT")
    elif a and b and not _compatible(
        left["dimensions"][name]["value"], right["dimensions"][name]["value"]
    ):
        hard.append(f"{label}_MISMATCH")


def _pair_score(left, right, hard, explicit, missing, source_counts):
    factors = {
        "USEFUL_CANONICAL": 2 if left["canonical_service"] else 0,
        "BOTH_PRICES": 2 if left["price"] and right["price"] else 0,
        "INDEPENDENT_PROVIDERS": 3 if left["provider_id"] != right["provider_id"] else 0,
        "SAME_CURRENCY": 2 if _same_known(left, right, "currency") else 0,
        "NO_HARD_BLOCKERS": 4 if not hard else 0,
        "FEW_BILATERAL_GAPS": 4 if len(missing) <= 4 else 2 if len(missing) <= 8 else 0,
        "REACQUIRABLE_SOURCES": 2 if left["source_url"] and right["source_url"] else 0,
        "SHARED_SOURCE_MULTIPLIER": min(3, source_counts[left["source"]] + source_counts[right["source"]] - 2),
        "HARD_BLOCKER_PENALTY": -10 * len(hard),
        "EXPLICIT_MISMATCH_PENALTY": -4 * len(explicit),
        "UNKNOWN_EVIDENCE_PENALTY": -min(8, len(missing)),
        "TEMPORAL_RISK_PENALTY": -sum(
            2 for item in (left, right) if item["temporal_status"] == "UNVERSIONED"
        ),
    }
    return sum(factors.values()), factors


def _build_actions(audits, pairs, registry, source_counts):
    unlockable = [item for item in pairs if item.compatibility_state is PairCompatibilityState.MISSING_EVIDENCE]
    requirements_by_source: dict[str, set[str]] = defaultdict(set)
    pairs_by_source: dict[str, set[str]] = defaultdict(set)
    audit_by_id = {item["observation_id"]: item for item in audits}
    for pair in unlockable:
        for requirement in pair.missing_evidence:
            source = audit_by_id[requirement.observation_id]["source"]
            requirements_by_source[source].add(requirement.claim_id)
            pairs_by_source[source].add(pair.pair_id)
    actions = []
    for source in sorted(requirements_by_source):
        claims = requirements_by_source[source]
        affected = pairs_by_source[source]
        expected = sum(
            set(item.missing_evidence_claim_ids).issubset(claims)
            for item in (_pair_proxy(pair) for pair in unlockable if pair.pair_id in affected)
        )
        source_audits = [item for item in audits if item["source"] == source]
        attribution = "MEDIUM" if len(source_audits) == 1 else "HIGH"
        temporal = "LOW" if all(item["temporal_status"] == "CURRENT_EXACT_OFFER" for item in source_audits) else "HIGH"
        factors = {
            "AFFECTED_PAIRS": min(5, len(affected)),
            "EXPECTED_PAIR_UNLOCK": expected * 6,
            "SHARED_SOURCE": 3 if source_counts[source] > 1 else 0,
            "LOCAL_OR_VERSIONED_RAW": 2 if any(item["temporal_status"] in {"CURRENT_EXACT_OFFER", "HISTORICAL_TRACEABLE"} for item in source_audits) else 0,
            "ZERO_DIRECT_UNLOCK_PENALTY": -6 if expected == 0 else 0,
            "ATTRIBUTION_RISK_PENALTY": -2 if attribution == "HIGH" else -1,
            "TEMPORAL_RISK_PENALTY": -2 if temporal == "HIGH" else 0,
        }
        actions.append({
            "schema_version": "cohort-pair-evidence-plan-v1",
            "action_id": f"pair-acq:{source}",
            "pair_ids_affected": sorted(affected),
            "cohort": DEFAULT_COHORT,
            "source": source,
            "source_url": registry[source]["url"],
            "target_observations": sorted((item["observation_id"] for item in source_audits), key=int),
            "target_dimensions": sorted({claim.split(":", 1)[1] for claim in claims}),
            "claims_potentially_resolved": sorted(claims),
            "minimal_unlock_contribution": len(claims),
            "expected_pairs_unlocked": expected,
            "expected_cohort_unlock": expected,
            "expected_independent_providers_gained": 0 if expected == 0 else len({item["provider_id"] for item in source_audits}),
            "could_enable_partial": False,
            "could_enable_ready": False,
            "request_deduplication_key": f"{source}|{registry[source]['url']}",
            "acquisition_method": "VERSIONED_RAW_REPROCESS" if factors["LOCAL_OR_VERSIONED_RAW"] else "NORMAL_HTTP_REACQUISITION",
            "acquisition_cost": "ZERO_NETWORK" if factors["LOCAL_OR_VERSIONED_RAW"] else "ONE_HTTP_REQUEST",
            "attribution_risk": attribution,
            "temporal_risk": temporal,
            "score_breakdown": factors,
            "expected_economic_value": sum(factors.values()),
        })
    actions.sort(key=lambda item: (-item["expected_pairs_unlocked"], -item["expected_economic_value"], item["source"]))
    for rank, action in enumerate(actions, 1):
        action["rank"] = rank
    return actions


class _PairProxy:
    def __init__(self, pair):
        self.missing_evidence_claim_ids = tuple(item.claim_id for item in pair.missing_evidence)


def _pair_proxy(pair):
    return _PairProxy(pair)


def _cohort_routes(pairs, by_id):
    if not pairs:
        return {"FIRST_PAIR": None, "FIRST_TWO_PROVIDERS": None, "PARTIAL": None, "READY": None}
    first = min(pairs, key=lambda item: (len(item.missing_evidence), -item.score, item.pair_id))
    return {
        "FIRST_PAIR": _route_payload((first,)),
        "FIRST_TWO_PROVIDERS": _route_payload((first,)),
        "PARTIAL": _best_star_route(pairs, by_id, 3, 2, Decimal("2.0")),
        "READY": _best_star_route(pairs, by_id, 5, 3, Decimal("2.5")),
    }


def _best_star_route(pairs, by_id, edge_count, provider_count, spread_limit):
    candidates = []
    for anchor in by_id:
        edges = [item for item in pairs if anchor in {item.observation_a, item.observation_b}]
        for selected in combinations(edges, edge_count):
            peers = [item.observation_b if item.observation_a == anchor else item.observation_a for item in selected]
            providers = {by_id[item]["provider_id"] for item in peers}
            prices = [Decimal(by_id[item]["price"]) for item in peers if Decimal(by_id[item]["price"]) > 0]
            if len(providers) < provider_count or not prices or max(prices) / min(prices) > spread_limit:
                continue
            claims = {claim.claim_id for pair in selected for claim in pair.missing_evidence}
            candidates.append((len(claims), anchor, tuple(item.pair_id for item in selected), claims))
    if not candidates:
        return None
    _, anchor, pair_ids, claims = min(candidates, key=lambda item: (item[0], int(item[1]), item[2]))
    return {"anchor": anchor, "pair_ids": list(pair_ids), "required_claims": sorted(claims), "claim_count": len(claims)}


def _route_payload(pairs):
    claims = {claim.claim_id for pair in pairs for claim in pair.missing_evidence}
    return {"pair_ids": [item.pair_id for item in pairs], "required_claims": sorted(claims), "claim_count": len(claims)}


def _cohort_readiness(pairs, by_id):
    adjacency = defaultdict(list)
    for pair in pairs:
        adjacency[pair.observation_a].append(pair.observation_b)
        adjacency[pair.observation_b].append(pair.observation_a)
    best = "INSUFFICIENT"
    for peers in adjacency.values():
        providers = {by_id[item]["provider_id"] for item in peers}
        prices = [Decimal(by_id[item]["price"]) for item in peers if Decimal(by_id[item]["price"]) > 0]
        spread = max(prices) / min(prices) if prices else Decimal("Infinity")
        if len(peers) >= 5 and len(providers) >= 3 and spread <= Decimal("2.5"):
            return "READY"
        if len(peers) >= 3 and len(providers) >= 2 and spread <= Decimal("2.0"):
            best = "PARTIAL"
    return best


def _metrics(audits, pairs, plan):
    missing_sizes = Counter()
    blockers = Counter()
    for pair in pairs:
        blockers.update(pair.hard_blockers)
        blockers.update(pair.explicit_mismatches)
        blockers.update(f"MISSING_{item.dimension.upper()}_{item.side}" for item in pair.missing_evidence)
        if pair.compatibility_state is PairCompatibilityState.MISSING_EVIDENCE:
            size = len(pair.missing_evidence)
            if size == 1:
                missing_sizes["MIN_UNLOCK_SIZE_1"] += 1
            elif size == 2:
                missing_sizes["MIN_UNLOCK_SIZE_2"] += 1
            elif size == 3:
                missing_sizes["MIN_UNLOCK_SIZE_3"] += 1
            elif size >= 4:
                missing_sizes["MIN_UNLOCK_SIZE_4_PLUS"] += 1
    return {
        "TOTAL_PAIR_CANDIDATES": len(pairs),
        "PAIR_HARD_BLOCKED": sum(item.compatibility_state is PairCompatibilityState.HARD_BLOCKED for item in pairs),
        "PAIR_EXPLICIT_MISMATCH": sum(item.compatibility_state is PairCompatibilityState.EXPLICIT_MISMATCH for item in pairs),
        "PAIR_MISSING_EVIDENCE": sum(item.compatibility_state is PairCompatibilityState.MISSING_EVIDENCE for item in pairs),
        "PAIR_POTENTIALLY_UNLOCKABLE": sum(item.compatibility_state is PairCompatibilityState.MISSING_EVIDENCE for item in pairs),
        "PAIR_COMPARABLE": sum(item.compatibility_state is PairCompatibilityState.COMPARABLE for item in pairs),
        "MIN_UNLOCK_SIZE_1": missing_sizes["MIN_UNLOCK_SIZE_1"],
        "MIN_UNLOCK_SIZE_2": missing_sizes["MIN_UNLOCK_SIZE_2"],
        "MIN_UNLOCK_SIZE_3": missing_sizes["MIN_UNLOCK_SIZE_3"],
        "MIN_UNLOCK_SIZE_4_PLUS": missing_sizes["MIN_UNLOCK_SIZE_4_PLUS"],
        "BLOCKER_DISTRIBUTION": dict(sorted(blockers.items())),
        "PLANNED_ACTIONS": len(plan),
    }


def _pair_payload(pair, rank):
    return {
        "schema_version": "economic-evidence-pair-v1",
        "rank": rank,
        **{key: _json_value(value) for key, value in asdict(pair).items()},
        "compatibility_state": pair.compatibility_state.value,
        "score_breakdown": dict(pair.score_breakdown),
        "missing_evidence": [_json_value(item) for item in pair.missing_evidence],
        "explanation": _explanation(pair),
    }


def _unlock_payload(unlock):
    return {"schema_version": "minimal-pair-unlock-set-v1", **_json_value(asdict(unlock))}


def _explanation(pair):
    return {
        "compatible": ["canonical", "independent_provider", "currency"] if not pair.hard_blockers else [],
        "hard_blockers": list(pair.hard_blockers),
        "explicit_mismatches": list(pair.explicit_mismatches),
        "missing_bilateral_evidence": [item.claim_id for item in pair.missing_evidence],
        "potential_state": pair.compatibility_state.value,
    }


def _provider_coverage(pairs):
    return len({provider for item in pairs for provider in (item.provider_a, item.provider_b)})


def _pair_temporal(left, right):
    if "TEMPORAL_MISMATCH" in {left["temporal_status"], right["temporal_status"]}:
        return "TEMPORAL_MISMATCH"
    if left["temporal_status"] == right["temporal_status"] == "CURRENT_EXACT_OFFER":
        return "CURRENT_IDENTITIES_PROVEN"
    return "UNKNOWN_NO_CROSS_VERSION_CLAIM_APPLIED"


def _same_known(left, right, name):
    return _usable(left, name) and _usable(right, name) and _compatible(
        left["dimensions"][name]["value"], right["dimensions"][name]["value"]
    )


def _usable(item, name):
    return item["dimensions"][name]["status"] in {"OBSERVED", "INFERRED"} and item["dimensions"][name]["value"] is not None


def _compatible(left, right):
    return _normalize(left) == _normalize(right)


def _normalize(value):
    if isinstance(value, list):
        return tuple(sorted(_normalize(item) for item in value))
    if isinstance(value, dict):
        return tuple(sorted((key, _normalize(item)) for key, item in value.items()))
    return value


def _dimension_payload(value):
    return {"status": value.status.value, "value": _json_value(value.value)}


def _json_value(value):
    if is_dataclass(value):
        return {key: _json_value(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return [_json_value(item) for item in sorted(value, key=repr)]
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if hasattr(value, "value") and hasattr(value, "name"):
        return value.value
    return value


def _csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _jsonl(path):
    source = Path(path)
    if not source.exists():
        return []
    return [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(_json_value(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
