from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.dominio.economic_evidence import DimensionStatus
from src.infraestructura.economic_dimensions_loader import (
    load_versioned_economic_dimensions_sidecar,
)


SCHEMA_VERSION = "economic-evidence-gap-register-v1"
USEFUL_ROLES = {"SINGLE_SERVICE", "COMPOSITE_SERVICE", "HARDWARE_PRODUCT"}
BLOCKER_NAMES = {
    "geographic_reach": "MISSING_REACH",
    "price_scope": "MISSING_PRICE_SCOPE",
    "provider_identity": "MISSING_PROVIDER",
    "currency": "MISSING_CURRENCY",
    "device_scope": "MISSING_DEVICE_SCOPE",
    "bundle_status": "MISSING_BUNDLE_INFO",
    "hardware_included": "MISSING_HARDWARE_INFO",
    "materials_included": "MISSING_MATERIALS_INFO",
    "delivery_mode": "MISSING_DELIVERY_MODE",
    "commercial_context": "MISSING_COMMERCIAL_CONTEXT",
}
CORE_DIMENSIONS = (
    "geographic_reach", "price_scope", "provider_identity", "currency",
    "device_scope", "bundle_status", "hardware_included",
)


def build_gap_register(
    normalization_path: str | Path,
    registry_path: str | Path,
    dimensions_path: str | Path,
    output_path: str | Path,
    *,
    version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    with Path(normalization_path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with Path(registry_path).open(encoding="utf-8-sig", newline="") as handle:
        registry = {row["source"].strip(): row for row in csv.DictReader(handle)}
    dimensions = load_versioned_economic_dimensions_sidecar(dimensions_path)
    ids = [row["observation_id"].strip() for row in rows]
    if set(ids) != set(dimensions) or len(ids) != len(set(ids)):
        raise ValueError("Gap register requires exact dimensions/input cardinality parity.")

    candidates = {
        row["observation_id"]: _potential_candidates(row, rows, dimensions)
        for row in rows
    }
    entries = []
    blocker_counts: Counter[str] = Counter()
    group_counts: dict[str, dict[str, Counter[str]]] = {
        field: defaultdict(Counter)
        for field in ("canonical_service", "provider", "source", "province", "semantic_role")
    }
    for row in rows:
        observation_id = row["observation_id"]
        item = dimensions[observation_id]
        blockers = []
        for name, dimension in item.all_dimensions().items():
            if dimension.status is DimensionStatus.UNKNOWN:
                blockers.append(BLOCKER_NAMES.get(name, f"MISSING_{name.upper()}"))
            elif dimension.status in {DimensionStatus.CONFLICTED, DimensionStatus.AMBIGUOUS}:
                blockers.append(f"CONFLICTED_{name.upper()}")
        blockers = sorted(set(blockers))
        blocker_counts.update(blockers)
        provider = str(registry.get(row["source"], {}).get("provider") or "UNKNOWN")
        values = {
            "canonical_service": row.get("canonical_service") or "UNKNOWN",
            "provider": provider,
            "source": row.get("source") or "UNKNOWN",
            "province": row.get("province") or "UNKNOWN",
            "semantic_role": row.get("semantic_role") or "UNKNOWN",
        }
        for field, value in values.items():
            group_counts[field][value].update(blockers)
        score, reasons = _priority(row, item, candidates[observation_id])
        entries.append({
            "schema_version": SCHEMA_VERSION,
            "version": version,
            "observation_id": observation_id,
            **values,
            "blockers": blockers,
            "core_gap_count": sum(
                item.all_dimensions()[name].status is not DimensionStatus.OBSERVED
                and item.all_dimensions()[name].status is not DimensionStatus.INFERRED
                for name in CORE_DIMENSIONS
            ),
            "potential_similar_candidates": candidates[observation_id],
            "acquisition_priority": score,
            "priority_reasons": reasons,
        })

    entries.sort(key=lambda entry: int(entry["observation_id"]))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    ranked = sorted(
        entries,
        key=lambda entry: (-entry["acquisition_priority"], entry["core_gap_count"], -entry["potential_similar_candidates"], int(entry["observation_id"])),
    )
    metrics: dict[str, Any] = {
        "TOTAL_OBSERVATIONS": len(entries),
        "BLOCKERS": dict(sorted(blocker_counts.items())),
        "NEAR_COMPARABLE_OBSERVATIONS": sum(entry["core_gap_count"] <= 2 and entry["potential_similar_candidates"] > 0 for entry in entries),
        "TOP_ACQUISITION_PRIORITIES": [
            {key: entry[key] for key in (
                "observation_id", "source", "canonical_service", "blockers",
                "core_gap_count", "potential_similar_candidates", "acquisition_priority",
                "priority_reasons",
            )}
            for entry in ranked[:20]
        ],
        "GAPS_BY_COHORT": {
            field: {
                value: dict(sorted(counter.items()))
                for value, counter in sorted(groups.items())
            }
            for field, groups in group_counts.items()
        },
        "PRIORITY_FORMULA": {
            "HAS_PRICE": 2,
            "ECONOMICALLY_USEFUL_ROLE": 2,
            "KNOWN_CANONICAL_SERVICE": 2,
            "KNOWN_PROVIDER": 1,
            "ONE_OR_TWO_CORE_GAPS": 3,
            "HAS_POTENTIAL_SIMILAR_CANDIDATES": 2,
        },
    }
    output.with_suffix(".summary.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "version": version, "metrics": metrics}, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return metrics


def _potential_candidates(row, rows, dimensions) -> int:
    canonical = row.get("canonical_service") or ""
    currency = row.get("currency") or ""
    if not canonical or not currency:
        return 0
    current = dimensions[row["observation_id"]]
    if current.currency.status in {DimensionStatus.CONFLICTED, DimensionStatus.AMBIGUOUS}:
        return 0
    count = 0
    for other in rows:
        if other["observation_id"] == row["observation_id"]:
            continue
        if other.get("canonical_service") != canonical or other.get("currency") != currency:
            continue
        if other.get("source") == row.get("source"):
            continue
        other_dimensions = dimensions[other["observation_id"]]
        if _known_dimensions_compatible(current, other_dimensions):
            count += 1
    return count


def _known_dimensions_compatible(left, right) -> bool:
    for name in ("device_scope", "bundle_status", "hardware_included"):
        a = left.all_dimensions()[name]
        b = right.all_dimensions()[name]
        if a.is_usable and b.is_usable and a.value != b.value:
            return False
    return True


def _priority(row, dimensions, candidate_count: int) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    for condition, points, reason in (
        (bool(str(row.get("price_value") or "").strip()), 2, "HAS_PRICE"),
        (row.get("semantic_role") in USEFUL_ROLES, 2, "ECONOMICALLY_USEFUL_ROLE"),
        (bool(str(row.get("canonical_service") or "").strip()), 2, "KNOWN_CANONICAL_SERVICE"),
        (dimensions.provider_identity.is_usable, 1, "KNOWN_PROVIDER"),
    ):
        if condition:
            score += points
            reasons.append(reason)
    core_gaps = sum(
        not dimensions.all_dimensions()[name].is_usable for name in CORE_DIMENSIONS
    )
    if 1 <= core_gaps <= 2:
        score += 3
        reasons.append("ONE_OR_TWO_CORE_GAPS")
    if candidate_count > 0:
        score += 2
        reasons.append("HAS_POTENTIAL_SIMILAR_CANDIDATES")
    return score, reasons
