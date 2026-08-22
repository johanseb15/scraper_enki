from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    DimensionValue,
    EconomicEvidenceDimensions,
    GeographyDimension,
    ProviderIdentity,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.infraestructura.economic_dimensions_adapter import (
    DIMENSIONS_VERSION,
    derive_economic_dimensions,
)


SIDECAR_SCHEMA_VERSION = "economic-evidence-dimensions-v1"


def build_economic_dimensions_sidecar(
    normalization_path: str | Path,
    registry_path: str | Path,
    output_path: str | Path,
    *,
    version: str = DIMENSIONS_VERSION,
) -> dict[str, Any]:
    with Path(normalization_path).open("r", encoding="utf-8-sig", newline="") as handle:
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
        raise ValueError("Every dimension sidecar row requires observation_id.")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate observation_id values in dimension input.")

    dimensions = [derive_economic_dimensions(row, registry) for row in rows]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for observation_id, value in zip(ids, dimensions, strict=True):
            payload = {
                "schema_version": SIDECAR_SCHEMA_VERSION,
                "version": version,
                "observation_id": observation_id,
                "dimensions": _dimensions_payload(value),
            }
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")

    metrics = build_dimension_metrics(dimensions)
    metrics["TOTAL_OBSERVATIONS"] = len(rows)
    metrics["OUTPUT_ROWS"] = len(dimensions)
    output.with_suffix(".summary.json").write_text(
        json.dumps(
            {
                "schema_version": SIDECAR_SCHEMA_VERSION,
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


def load_economic_dimensions_sidecar(
    path: str | Path,
) -> dict[str, EconomicEvidenceDimensions]:
    result = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("schema_version") != SIDECAR_SCHEMA_VERSION:
            raise ValueError(f"Unsupported dimension schema at line {line_number}.")
        observation_id = str(payload.get("observation_id") or "").strip()
        if not observation_id or observation_id in result:
            raise ValueError(f"Invalid or duplicate observation_id at line {line_number}.")
        result[observation_id] = _dimensions_from_payload(payload["dimensions"])
    return result


def build_dimension_metrics(
    dimensions: Iterable[EconomicEvidenceDimensions],
) -> dict[str, dict[str, int]]:
    counters = {
        status: Counter()
        for status in DimensionStatus
    }
    for item in dimensions:
        for name, value in item.all_dimensions().items():
            counters[value.status][name] += 1
    metrics = {
        f"{status.value}_DIMENSIONS": dict(sorted(counters[status].items()))
        for status in DimensionStatus
    }
    metrics["EXPLICIT_DIMENSIONS"] = dict(metrics["OBSERVED_DIMENSIONS"])
    return metrics


def _dimensions_payload(value: EconomicEvidenceDimensions) -> dict[str, Any]:
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


def _dimensions_from_payload(payload: Mapping[str, Any]) -> EconomicEvidenceDimensions:
    values = {
        name: _dimension_from_payload(name, payload[name])
        for name in EconomicEvidenceDimensions().all_dimensions()
    }
    return EconomicEvidenceDimensions(**values)


def _dimension_from_payload(name: str, payload: Mapping[str, Any]) -> DimensionValue[object]:
    claims = tuple(
        DimensionClaim(
            value=_typed_value(name, item["value"]),
            origin=DimensionOrigin(item["origin"]),
            provenance=KnowledgeProvenance(**item["provenance"]),
            raw_basis=item["raw_basis"],
        )
        for item in payload.get("claims", [])
    )
    return DimensionValue(
        value=_typed_value(name, payload.get("value")),
        status=DimensionStatus(payload["status"]),
        claims=claims,
    )


def _typed_value(name: str, value: Any) -> Any:
    if value is None:
        return None
    if name == "provider_identity":
        return ProviderIdentity(**value)
    if name == "geography":
        return GeographyDimension(**value)
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
