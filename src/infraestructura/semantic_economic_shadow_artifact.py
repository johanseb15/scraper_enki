from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from src.dominio.economic_evidence import EconomicEvidenceContext


SHADOW_SCHEMA_VERSION = "semantic-economic-shadow-v1"


def write_semantic_economic_shadow_jsonl(
    contexts: Iterable[EconomicEvidenceContext],
    output_path: str | Path,
    *,
    version: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for context in contexts:
            payload = _context_payload(context, version=version)
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    return path


def build_shadow_metrics(
    contexts: Iterable[EconomicEvidenceContext],
) -> dict[str, Any]:
    items = tuple(contexts)
    readiness = Counter(item.readiness.value for item in items)
    exclusions = Counter(
        reason.value
        for item in items
        for excluded in item.excluded_evidence
        for reason in excluded.reasons
    )
    resolved = sum(bool(item.comparable_evidence) for item in items)
    return {
        "TOTAL_OBSERVATIONS": len(items),
        "EVIDENCE_RESOLVED": resolved,
        "NO_EVIDENCE": len(items) - resolved,
        "READY": readiness["READY"],
        "PARTIAL": readiness["PARTIAL"],
        "INSUFFICIENT": readiness["INSUFFICIENT"],
        "AMBIGUOUS": readiness["AMBIGUOUS"],
        "UNKNOWN": readiness["UNKNOWN"],
        "TOTAL_CANDIDATE_EVIDENCE": sum(len(item.candidate_evidence) for item in items),
        "TOTAL_COMPARABLE_EVIDENCE": sum(len(item.comparable_evidence) for item in items),
        "TOTAL_EXCLUDED_EVIDENCE": sum(len(item.excluded_evidence) for item in items),
        "EXCLUSION_REASONS": dict(sorted(exclusions.items())),
    }


def write_shadow_summary(
    metrics: dict[str, Any],
    output_path: str | Path,
    *,
    version: str,
) -> Path:
    path = Path(output_path)
    payload = {
        "schema_version": SHADOW_SCHEMA_VERSION,
        "version": version,
        "metrics": metrics,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _context_payload(context: EconomicEvidenceContext, *, version: str) -> dict[str, Any]:
    return {
        "schema_version": SHADOW_SCHEMA_VERSION,
        "version": version,
        "observation_id": context.observation_id,
        "economic_object_kind": context.economic_object_kind.value,
        "semantic_role": context.semantic_role.value,
        "understanding_status": context.understanding_status.value,
        "canonical_service": context.canonical_service,
        "matched_services": list(context.matched_services),
        "readiness": context.readiness.value,
        "evidence_count": context.evidence_count,
        "independent_provider_count": context.independent_provider_count,
        "geography_scope": context.geography_scope,
        "price_scope": context.price_scope,
        "missing_dimensions": list(context.missing_dimensions),
        "uncertainty": list(context.uncertainty),
        "conflicted_dimensions": list(context.conflicted_dimensions),
        "candidate_evidence_ids": [item.evidence_id for item in context.candidate_evidence],
        "comparable_evidence": [_evidence_payload(item) for item in context.comparable_evidence],
        "excluded_evidence": [
            {
                "evidence_id": item.evidence.evidence_id,
                "provider": item.evidence.provider,
                "reasons": [reason.value for reason in item.reasons],
            }
            for item in context.excluded_evidence
        ],
        "provenance": [_jsonable(item) for item in context.provenance],
    }


def _evidence_payload(value) -> dict[str, Any]:
    return {
        "evidence_id": value.evidence_id,
        "provider": value.provider,
        "currency": value.currency,
        "price_value": str(value.price_value) if value.price_value is not None else None,
        "price_scope": value.price_scope,
        "market_scope": value.market_scope,
        "province": value.province,
        "provenance": _jsonable(value.provenance),
        "dimensions": _jsonable(value.dimensions),
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, frozenset):
        return sorted(_jsonable(item) for item in value)
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
