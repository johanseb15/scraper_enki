from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    DimensionValue,
    EconomicEvidenceDimensionsV2,
    LocationDimension,
    ProviderIdentity,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.infraestructura.economic_dimensions_artifact import (
    load_economic_dimensions_sidecar,
)
from src.infraestructura.economic_dimensions_v2_adapter import (
    DIMENSIONS_V2_VERSION,
    derive_economic_dimensions_v2,
)


SIDECAR_V2_SCHEMA_VERSION = "economic-evidence-dimensions-v2"


def _known(value: str) -> str | None:
    return None if not value or value.upper() in {"UNKNOWN", "NONE", "N/A"} else value


def build_economic_dimensions_v2_sidecar(
    normalization_path: str | Path,
    registry_path: str | Path,
    output_path: str | Path,
    *,
    version: str = DIMENSIONS_V2_VERSION,
    previous_dimensions_path: str | Path | None = None,
) -> dict[str, Any]:
    normalization = Path(normalization_path)
    with normalization.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with Path(registry_path).open("r", encoding="utf-8-sig", newline="") as handle:
        registry_rows = list(csv.DictReader(handle))
    registry = {
        str(row.get("source") or "").strip(): row
        for row in registry_rows
        if str(row.get("source") or "").strip()
    }
    ids = [str(row.get("observation_id") or "").strip() for row in rows]
    if any(not value for value in ids):
        raise ValueError("Every v2 dimension row requires observation_id.")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate observation_id values in v2 dimension input.")

    dimensions = [derive_economic_dimensions_v2(row, registry) for row in rows]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for observation_id, value in zip(ids, dimensions, strict=True):
            payload = {
                "schema_version": SIDECAR_V2_SCHEMA_VERSION,
                "version": version,
                "observation_id": observation_id,
                "dimensions": _dimensions_payload(value),
            }
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")

    metrics = build_v2_dimension_metrics(dimensions, rows)
    if previous_dimensions_path is not None:
        previous = load_economic_dimensions_sidecar(previous_dimensions_path)
        if set(previous) != set(ids):
            raise ValueError("Previous v1 sidecar observation ids do not match v2 input.")
        metrics.update(build_migration_metrics(previous, dict(zip(ids, dimensions, strict=True))))
    else:
        metrics.update({
            "FALSE_CONFLICTS_REMOVED": 0,
            "REAL_CONFLICTS_PRESERVED": 0,
        })
    metrics["TOTAL_OBSERVATIONS"] = len(rows)
    metrics["OUTPUT_ROWS"] = len(dimensions)
    output.with_suffix(".summary.json").write_text(
        json.dumps(
            {
                "schema_version": SIDECAR_V2_SCHEMA_VERSION,
                "version": version,
                "metrics": metrics,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return metrics


def load_economic_dimensions_v2_sidecar(
    path: str | Path,
) -> dict[str, EconomicEvidenceDimensionsV2]:
    result = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("schema_version") != SIDECAR_V2_SCHEMA_VERSION:
            raise ValueError(f"Unsupported v2 dimension schema at line {line_number}.")
        observation_id = str(payload.get("observation_id") or "").strip()
        if not observation_id or observation_id in result:
            raise ValueError(f"Invalid or duplicate observation_id at line {line_number}.")
        result[observation_id] = _dimensions_from_payload(payload["dimensions"])
    return result


def build_v2_dimension_metrics(
    dimensions: Iterable[EconomicEvidenceDimensionsV2],
    rows: Iterable[Mapping[str, object]],
) -> dict[str, Any]:
    items = tuple(dimensions)
    row_items = tuple(rows)
    counters = {status: Counter() for status in DimensionStatus}
    conflict_audit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ambiguity_audit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row, item in zip(row_items, items, strict=True):
        for name, value in item.all_dimensions().items():
            counters[value.status][name] += 1
            if value.status in {DimensionStatus.CONFLICTED, DimensionStatus.AMBIGUOUS}:
                target = conflict_audit if value.status is DimensionStatus.CONFLICTED else ambiguity_audit
                target[name].append(_audit_entry(row, value))
    metrics: dict[str, Any] = {
        f"{status.value}_DIMENSIONS": dict(sorted(counters[status].items()))
        for status in DimensionStatus
    }
    metrics["CONFLICTS_BY_DIMENSION"] = dict(metrics["CONFLICTED_DIMENSIONS"])
    metrics["AMBIGUITIES_BY_DIMENSION"] = dict(metrics["AMBIGUOUS_DIMENSIONS"])
    metrics["CONFLICT_AUDIT"] = dict(sorted(conflict_audit.items()))
    metrics["AMBIGUITY_AUDIT"] = dict(sorted(ambiguity_audit.items()))
    metrics["MULTIVALUE_CONTEXTS"] = sum(
        value.commercial_context.is_usable
        and value.commercial_context.value is not None
        and len(value.commercial_context.value) > 1
        for value in items
    )
    metrics["ORTHOGONAL_DIMENSION_SPLITS"] = sum(
        item.delivery_mode.is_usable
        and _known(str(row.get("market_scope") or "")) is not None
        for row, item in zip(row_items, items, strict=True)
    )
    return metrics


def build_migration_metrics(previous, current) -> dict[str, int]:
    false_removed = 0
    real_preserved = 0
    for observation_id, old in previous.items():
        new = current[observation_id]
        for name, dimension in old.all_dimensions().items():
            if dimension.status not in {DimensionStatus.CONFLICTED, DimensionStatus.AMBIGUOUS}:
                continue
            values = {claim.value for claim in dimension.claims}
            if name == "market_scope" and values.intersection({"REMOTE", "ONSITE"}):
                false_removed += 1
            elif (
                name == "commercial_context"
                and dimension.status is DimensionStatus.AMBIGUOUS
                and new.commercial_context.is_usable
                and new.commercial_context.value is not None
                and len(new.commercial_context.value) > 1
            ):
                false_removed += 1
            else:
                new_dimension = new.all_dimensions().get(name)
                if new_dimension is not None and new_dimension.status in {
                    DimensionStatus.CONFLICTED,
                    DimensionStatus.AMBIGUOUS,
                }:
                    real_preserved += 1
    return {
        "FALSE_CONFLICTS_REMOVED": false_removed,
        "REAL_CONFLICTS_PRESERVED": real_preserved,
    }


def _audit_entry(row: Mapping[str, object], value: DimensionValue[object]) -> dict[str, Any]:
    return {
        "observation_id": str(row.get("observation_id") or ""),
        "raw_expression": str(row.get("economic_object_raw") or ""),
        "values": [_jsonable(claim.value) for claim in value.claims],
        "claims": [
            {
                "value": _jsonable(claim.value),
                "origin": claim.origin.value,
                "raw_basis": claim.raw_basis,
                "provenance": _jsonable(claim.provenance),
            }
            for claim in value.claims
        ],
    }


def _dimensions_payload(value: EconomicEvidenceDimensionsV2) -> dict[str, Any]:
    return {
        name: _dimension_payload(dimension)
        for name, dimension in value.all_dimensions().items()
    }


def _dimension_payload(value: DimensionValue[object]) -> dict[str, Any]:
    return {
        "status": value.status.value,
        "value": _jsonable(value.value),
        "claims": [
            {
                "value": _jsonable(claim.value),
                "origin": claim.origin.value,
                "provenance": _jsonable(claim.provenance),
                "raw_basis": claim.raw_basis,
            }
            for claim in value.claims
        ],
    }


def _dimensions_from_payload(payload: Mapping[str, Any]) -> EconomicEvidenceDimensionsV2:
    values = {
        name: _dimension_from_payload(name, payload[name])
        for name in EconomicEvidenceDimensionsV2().all_dimensions()
    }
    return EconomicEvidenceDimensionsV2(**values)


def _dimension_from_payload(name: str, payload: Mapping[str, Any]) -> DimensionValue[object]:
    claims = tuple(
        DimensionClaim(
            value=_typed_value(name, item["value"], claim=True),
            origin=DimensionOrigin(item["origin"]),
            provenance=KnowledgeProvenance(**item["provenance"]),
            raw_basis=item["raw_basis"],
        )
        for item in payload.get("claims", [])
    )
    return DimensionValue(
        value=_typed_value(name, payload.get("value"), claim=False),
        status=DimensionStatus(payload["status"]),
        claims=claims,
    )


def _typed_value(name: str, value: Any, *, claim: bool) -> Any:
    if value is None:
        return None
    if name == "provider_identity":
        return ProviderIdentity(**value)
    if name == "location":
        return LocationDimension(**value)
    if name in {"commercial_context", "device_scope"} and not claim:
        return frozenset(value)
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, frozenset):
        return sorted(_jsonable(item) for item in value)
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
