from __future__ import annotations

from collections.abc import Mapping

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_knowledge_candidate import unknown_interpretation_provenance
from src.dominio.semantic_observation import SemanticObservation, SemanticObservationRole


class SemanticObservationAdapterError(ValueError):
    pass


def semantic_observation_from_normalized_row(
    row: Mapping[str, str],
    *,
    observation_row: Mapping[str, str] | None = None,
    interpretation_reference: str | None = None,
    interpretation_version: str | None = None,
) -> SemanticObservation:
    observation_row = observation_row or {}
    role = _semantic_role(row)
    canonical_service = _clean(row.get("canonical_service")) or None
    matched_services = _matched_services(row.get("matched_services"))

    return SemanticObservation(
        observation_id=_required(row, "observation_id"),
        raw_expression=_required(row, "economic_object_raw"),
        semantic_role=role,
        market_scope=_clean(row.get("market_scope")) or "UNKNOWN",
        source=_required(row, "source"),
        provider=_clean(observation_row.get("provider")) or _required(row, "source"),
        province=_clean(row.get("province")) or _clean(observation_row.get("province")) or None,
        canonical_service=canonical_service,
        matched_services=matched_services,
        observation_provenance=_observation_provenance(row, observation_row),
        interpretation_provenance=_interpretation_provenance(
            interpretation_reference,
            interpretation_version,
        ),
    )


def _semantic_role(row: Mapping[str, str]) -> SemanticObservationRole:
    raw_role = _required(row, "semantic_role")
    try:
        return SemanticObservationRole(raw_role)
    except ValueError as exc:
        raise SemanticObservationAdapterError(
            f"Unknown semantic_role for observation_id={_clean(row.get('observation_id'))}: {raw_role}"
        ) from exc


def _observation_provenance(
    row: Mapping[str, str],
    observation_row: Mapping[str, str],
) -> KnowledgeProvenance:
    source = _required(row, "source")
    observation_id = _required(row, "observation_id")
    source_url = _clean(observation_row.get("source_url"))
    reference = f"source={source};observation_id={observation_id}"
    if source_url:
        reference = f"{reference};url={source_url}"
    return KnowledgeProvenance(
        origin_type="COMMERCIAL_OBSERVATION",
        origin_reference=reference,
        origin_version=_clean(row.get("extractor_version")) or None,
    )


def _interpretation_provenance(
    interpretation_reference: str | None,
    interpretation_version: str | None,
) -> KnowledgeProvenance:
    if not _clean(interpretation_reference):
        return unknown_interpretation_provenance()
    return KnowledgeProvenance(
        origin_type="SEMANTIC_NORMALIZATION",
        origin_reference=_clean(interpretation_reference),
        origin_version=_clean(interpretation_version) or None,
    )


def _matched_services(value: object) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value or "").split("|") if part.strip())


def _required(row: Mapping[str, str], field: str) -> str:
    value = _clean(row.get(field))
    if not value:
        raise SemanticObservationAdapterError(f"Missing required field: {field}")
    return value


def _clean(value: object) -> str:
    return str(value or "").strip()
