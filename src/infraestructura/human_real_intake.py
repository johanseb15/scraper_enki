from __future__ import annotations

from dataclasses import asdict
from enum import Enum
import hashlib
import json
from pathlib import Path

from src.dominio.real_world_query_trace import InputModality
from src.infraestructura.real_world_query_tracer import append_trace, trace_real_world_query


class FounderFeedbackLabel(str, Enum):
    CORRECT = "CORRECT"
    WRONG = "WRONG"
    INCOMPLETE = "INCOMPLETE"
    MISUNDERSTOOD = "MISUNDERSTOOD"
    UNREALISTIC_PRICE = "UNREALISTIC_PRICE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    MISSING_CONTEXT = "MISSING_CONTEXT"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


def ingest_human_real_case(
    *, case_path, trace_path, raw_user_input, case_id, received_at,
    local_cohortes, remote_cohortes, founder_note=None, expected_intent=None,
    expected_normalization=None, observed_problem=None, real_world_outcome=None,
):
    trace = trace_real_world_query(
        raw_user_input, local_cohortes=local_cohortes, remote_cohortes=remote_cohortes,
        source_case_id=case_id, case_origin="HUMAN_REAL", input_modality=InputModality.TEXT,
        provenance=("founder-field-intake",), received_at=received_at,
        request_context={"field_case_id": case_id},
    )
    case = {
        "schema_version": "human-real-field-case-v1", "case_id": case_id,
        "trace_id": trace.trace_id, "source_type": "HUMAN_REAL", "received_at": received_at,
        "raw_user_input": raw_user_input, "founder_feedback": {
            "founder_note": founder_note, "expected_intent": expected_intent,
            "expected_normalization": expected_normalization, "observed_problem": observed_problem,
            "real_world_outcome": real_world_outcome,
            "epistemic_role": "HUMAN_FEEDBACK_NOT_PROMOTED_TRUTH",
        },
        "promotion_authorized": False,
    }
    _append_unique(case_path, case, "case_id")
    append_trace(trace_path, trace)
    return trace, case


def append_founder_feedback(path, *, trace_id, received_at, labels, note=None):
    normalized = tuple(sorted({FounderFeedbackLabel(value).value for value in labels}))
    identity = json.dumps({"labels": normalized, "note": note, "received_at": received_at, "trace_id": trace_id}, sort_keys=True, separators=(",", ":"))
    event = {
        "schema_version": "human-real-founder-feedback-v1",
        "feedback_event_id": "founder-feedback:" + hashlib.sha256(identity.encode()).hexdigest()[:24],
        "trace_id": trace_id, "received_at": received_at, "labels": list(normalized), "note": note,
        "epistemic_role": "HUMAN_FEEDBACK_NOT_PROMOTED_TRUTH", "promotion_authorized": False,
    }
    _append_unique(path, event, "feedback_event_id")
    return event


def field_coverage(case, trace):
    expected = case["founder_feedback"].get("expected_normalization")
    extracted = {item.field for item in trace.normalized_entities}
    explicit = set(expected or {})
    normalized = {field for field in explicit if field in extracted}
    lost = explicit - normalized
    return {
        "fields_explicit_in_input": len(explicit) if expected is not None else None,
        "fields_extracted": len(extracted), "fields_normalized": len(normalized) if expected is not None else None,
        "fields_unknown": len(trace.unknown_dimensions), "fields_lost": len(lost) if expected is not None else None,
        "fields_incorrect": None,
        "explicit_normalization_recall": (len(normalized) / len(explicit)) if explicit else None,
        "ground_truth_reviewed": expected is not None,
    }


def _append_unique(path, payload, identity_field):
    path = Path(path); rows = _jsonl(path)
    existing = next((item for item in rows if item[identity_field] == payload[identity_field]), None)
    if existing is not None and existing != payload:
        raise ValueError(f"Append-only identity collision: {payload[identity_field]}")
    if existing is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def _jsonl(path):
    path = Path(path)
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
