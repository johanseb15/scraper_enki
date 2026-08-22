from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.dominio.economic_evidence import DimensionStatus
from src.infraestructura.economic_dimensions_loader import load_versioned_economic_dimensions_sidecar


TARGET_IDS = ("62", "68", "69", "70", "234")
CORE_TARGETS = {
    "MISSING_REACH": "geographic_reach",
    "MISSING_PRICE_SCOPE": "price_scope",
    "MISSING_HARDWARE_INFO": "hardware_included",
    "MISSING_MATERIALS_INFO": "materials_included",
    "MISSING_DELIVERY_MODE": "delivery_mode",
    "MISSING_COMMERCIAL_CONTEXT": "commercial_context",
}
REQUIRED_PAIR_DIMENSIONS = (
    "currency", "price_scope", "delivery_mode", "geographic_reach",
    "commercial_context", "bundle_status",
)


def build_target_dossier_and_plan(
    normalization_path: str | Path,
    registry_path: str | Path,
    dimensions_path: str | Path,
    gap_path: str | Path,
    shadow_path: str | Path,
    dossier_path: str | Path,
    unlock_path: str | Path,
    plan_path: str | Path,
) -> dict[str, Any]:
    rows = _csv_by_id(normalization_path)
    registry = _csv_by_key(registry_path, "source")
    dimensions = load_versioned_economic_dimensions_sidecar(dimensions_path)
    gaps = _jsonl_by_id(gap_path)
    shadow = _jsonl_by_id(shadow_path)
    dossier = []
    unlocks = []
    actions = []
    for observation_id in TARGET_IDS:
        row = rows[observation_id]
        dim = dimensions[observation_id]
        gap = gaps[observation_id]
        context = shadow[observation_id]
        reg = registry[row["source"]]
        candidate_providers = {
            item["provider"] for item in context["excluded_evidence"]
            if item["evidence_id"] != observation_id
        }
        dossier.append({
            "schema_version": "near-comparable-target-dossier-v1",
            "observation_id": observation_id,
            "raw_economic_expression": row["economic_object_raw"],
            "canonical_service": row["canonical_service"],
            "semantic_role": row["semantic_role"],
            "provider_id": _value(dim, "provider_identity", "provider_id"),
            "provider_name": reg["provider"],
            "source": row["source"],
            "source_url": reg["url"],
            "price": row["price_value"],
            "currency": row["currency"],
            "dimensions": {name: _json_value(value) for name, value in dim.all_dimensions().items()},
            "candidate_evidence_count": len(context["candidate_evidence_ids"]),
            "candidate_exclusions": context["excluded_evidence"],
            "comparable_evidence_ids": context["comparable_evidence"],
            "missing_core_dimensions": [CORE_TARGETS[b] for b in gap["blockers"] if b in CORE_TARGETS],
            "all_blockers": gap["blockers"],
            "independent_candidate_providers": len(candidate_providers),
            "current_readiness": context["readiness"],
            "needed_for_comparability": _needed_for_comparability(dim),
        })
        target_dimensions = tuple(
            CORE_TARGETS[blocker] for blocker in gap["blockers"]
            if blocker in {"MISSING_REACH", "MISSING_HARDWARE_INFO"}
        )
        scenarios = [*( (name,) for name in target_dimensions )]
        if len(target_dimensions) > 1:
            scenarios.append(target_dimensions)
        for scenario in scenarios:
            potential = _counterfactual(row, dim, rows, dimensions, scenario)
            unlocks.append(potential)
            if len(scenario) == 1:
                score, breakdown = _score(
                    row, reg, dim, gap, potential, scenario[0],
                    has_local_raw=row["source"] == "bairescloud_generic",
                    shared_source=row["source"] == "bairescloud_generic",
                )
                actions.append({
                    "schema_version": "evidence-acquisition-plan-v1",
                    "action_id": f"acq:{observation_id}:{scenario[0]}",
                    "observation_id": observation_id,
                    "provider": reg["provider"],
                    "source": row["source"],
                    "source_url": reg["url"],
                    "target_dimension": scenario[0],
                    "reason": potential["explanation"],
                    "unlock_potential": potential["potentially_unlocked_pairs"],
                    "expected_economic_value": score,
                    "score_breakdown": breakdown,
                    "acquisition_method": "NORMAL_HTTP_REACQUISITION",
                    "estimated_risk": "LOW" if row["source"] == "bairescloud_generic" else "MEDIUM",
                    "current_blockers": gap["blockers"],
                    "blockers_if_success": potential["remaining_blockers"],
                    "evidence_needed": _evidence_needed(scenario[0]),
                    "provenance": "economic_evidence_gap_register_v1 + counterfactual-v1",
                })
    actions.sort(key=lambda item: (-item["expected_economic_value"], -item["unlock_potential"], int(item["observation_id"]), item["target_dimension"]))
    for rank, action in enumerate(actions, 1):
        action["rank"] = rank
    _write_jsonl(dossier_path, dossier)
    _write_jsonl(unlock_path, unlocks)
    _write_jsonl(plan_path, actions)
    return {
        "TARGETS_AUDITED": len(dossier),
        "COUNTERFACTUAL_SCENARIOS": len(unlocks),
        "ACQUISITION_ACTIONS": len(actions),
        "UNIQUE_SOURCES": len({item["source"] for item in actions}),
        "UNIQUE_URLS": len({item["source_url"] for item in actions}),
        "POTENTIALLY_UNLOCKED_PAIRS": sum(item["potentially_unlocked_pairs"] for item in unlocks),
    }


def _counterfactual(row, anchor, rows, dimensions, assumed: tuple[str, ...]) -> dict[str, Any]:
    providers = set()
    pairs = 0
    remaining = Counter()
    candidates = 0
    for other in rows.values():
        if other["observation_id"] == row["observation_id"] or other["source"] == row["source"]:
            continue
        if other["canonical_service"] != row["canonical_service"]:
            continue
        candidates += 1
        blockers = _pair_blockers(anchor, dimensions[other["observation_id"]], assumed)
        if blockers:
            remaining.update(blockers)
        else:
            pairs += 1
            providers.add(other["source"])
    remaining_names = tuple(sorted(remaining))
    max_readiness = "READY" if pairs >= 5 and len(providers) >= 3 else "PARTIAL" if pairs >= 3 and len(providers) >= 2 else "INSUFFICIENT"
    return {
        "schema_version": "acquisition-unlock-potential-v1",
        "observation_id": row["observation_id"],
        "missing_dimensions": list(assumed),
        "candidate_count": candidates,
        "potentially_unlocked_pairs": pairs,
        "potentially_unlocked_independent_providers": len(providers),
        "remaining_blockers": list(remaining_names),
        "max_possible_readiness": max_readiness,
        "explanation": (
            f"Assuming only {', '.join(assumed)} became compatible leaves "
            f"{len(remaining_names)} peer blocker types; no value is invented."
        ),
    }


def _pair_blockers(left, right, assumed: tuple[str, ...]) -> tuple[str, ...]:
    blockers = []
    for name in REQUIRED_PAIR_DIMENSIONS:
        if name in assumed:
            continue
        a, b = left.all_dimensions()[name], right.all_dimensions()[name]
        if not a.is_usable or not b.is_usable:
            blockers.append(f"UNKNOWN_{name.upper()}")
        elif a.value != b.value:
            blockers.append(f"MISMATCH_{name.upper()}")
    if _usable_value(left, "delivery_mode") == _usable_value(right, "delivery_mode") == "ONSITE":
        if "location" not in assumed and _usable_value(left, "location") != _usable_value(right, "location"):
            blockers.append("MISMATCH_LOCATION")
    for name in ("device_scope", "hardware_included", "materials_included"):
        if name in assumed:
            continue
        a, b = left.all_dimensions()[name], right.all_dimensions()[name]
        if a.is_usable != b.is_usable:
            blockers.append(f"UNKNOWN_{name.upper()}")
        elif a.is_usable and a.value != b.value:
            blockers.append(f"MISMATCH_{name.upper()}")
    return tuple(sorted(set(blockers)))


def _score(row, registry, dimensions, gap, potential, target_dimension, has_local_raw, shared_source):
    dimension_values = dimensions.all_dimensions()
    remaining = set(potential["remaining_blockers"])
    factors = {
        "PRICE_EXISTS": 2 if row["price_value"] else 0,
        "CANONICAL_KNOWN": 2 if row["canonical_service"] else 0,
        "PROVIDER_KNOWN": 1 if registry.get("provider") else 0,
        "SIMILAR_CANDIDATES": min(3, int(gap["potential_similar_candidates"])),
        "ONE_OR_TWO_CORE_GAPS": 3 if int(gap["core_gap_count"]) <= 2 else 0,
        "READINESS_POTENTIAL": 3 if potential["max_possible_readiness"] in {"PARTIAL", "READY"} else 0,
        "SOURCE_REACQUIRABLE": 2,
        "LOCAL_RAW_AVAILABLE": 1 if has_local_raw else 0,
        "SHARED_SOURCE_BENEFIT": 1 if shared_source else 0,
        "ZERO_UNLOCK_PENALTY": -4 if potential["potentially_unlocked_pairs"] == 0 else 0,
        "REMAINING_BLOCKERS_PENALTY": -min(3, len(potential["remaining_blockers"])),
        "SOURCE_BLOCKED_PENALTY": 0,
        "STALE_EVIDENCE_PENALTY": 0,
        "AMBIGUITY_PENALTY": -2 if any(value.status is DimensionStatus.AMBIGUOUS for value in dimension_values.values()) else 0,
        "CURRENCY_CONFLICT_PENALTY": -3 if dimension_values["currency"].status is DimensionStatus.CONFLICTED else 0,
        "BUNDLE_CONFLICT_PENALTY": -2 if any("BUNDLE_STATUS" in value for value in remaining) else 0,
        "HARDWARE_SERVICE_BOUNDARY_PENALTY": -2 if target_dimension == "hardware_included" else 0,
        "ISOLATED_OBSERVATION_PENALTY": -2 if potential["candidate_count"] <= 1 else 0,
    }
    return sum(factors.values()), factors


def _needed_for_comparability(dim):
    return [name for name in REQUIRED_PAIR_DIMENSIONS if not dim.all_dimensions()[name].is_usable]


def _evidence_needed(name):
    return {
        "geographic_reach": "Offer-attributable explicit service coverage or restriction.",
        "hardware_included": "Offer-attributable explicit hardware/replacement inclusion or exclusion.",
    }.get(name, f"Offer-attributable explicit {name}.")


def _usable_value(dim, name):
    value = dim.all_dimensions()[name]
    return value.value if value.is_usable else None


def _value(dim, name, attribute):
    value = dim.all_dimensions()[name]
    return getattr(value.value, attribute) if value.is_usable else None


def _json_value(value):
    if not value.is_usable:
        return {"status": value.status.value, "value": None}
    raw = value.value
    if hasattr(raw, "__dict__"):
        raw = raw.__dict__
    elif isinstance(raw, frozenset):
        raw = sorted(raw)
    return {"status": value.status.value, "value": raw}


def _csv_by_id(path):
    return _csv_by_key(path, "observation_id")


def _csv_by_key(path, key):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return {row[key].strip(): row for row in csv.DictReader(handle)}


def _jsonl_by_id(path):
    return {item["observation_id"]: item for item in (json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip())}


def _write_jsonl(path, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
