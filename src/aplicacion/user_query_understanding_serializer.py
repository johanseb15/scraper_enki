from __future__ import annotations

from enum import Enum

from src.dominio.user_query_understanding import (
    UserQueryUnderstandingEnvelope,
)


TRACE_SCHEMA_VERSION = (
    "user-query-understanding-trace-v1"
)


def serialize_user_query_understanding(
    envelope: UserQueryUnderstandingEnvelope,
) -> dict:
    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "raw_text": envelope.raw_text,
        "context": envelope.context.value,
        "status": envelope.status.value,
        "facts": [
            {
                "field": item.field,
                "value": _json_value(item.value),
                "origin": item.origin.value,
                "provenance": _provenance(
                    item.provenance
                ),
            }
            for item in envelope.facts
        ],
        "relations": [
            {
                "subject": item.subject,
                "predicate": item.predicate,
                "object": item.object,
                "provenance": _provenance(
                    item.provenance
                ),
            }
            for item in envelope.relations
        ],
        "unknowns": list(
            envelope.unknowns
        ),
        "clarification_reasons": list(
            envelope.clarification_reasons
        ),
        "raw_provenance": _provenance(
            envelope.raw_provenance
        ),
        "interpretation_provenance": _provenance(
            envelope.interpretation_provenance
        ),
        "projection_provenance": _provenance(
            envelope.projection_provenance
        ),
    }


def _provenance(value) -> dict:
    return {
        "origin_type": value.origin_type,
        "origin_reference": value.origin_reference,
        "origin_version": value.origin_version,
    }


def _json_value(value):
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, tuple):
        return [
            _json_value(item)
            for item in value
        ]

    if isinstance(value, list):
        return [
            _json_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: _json_value(item)
            for key, item in value.items()
        }

    return value
