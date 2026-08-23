from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class TraceStage(str, Enum):
    INGEST = "INGEST"
    PARSE = "PARSE"
    INTENT = "INTENT"
    SEMANTIC_NORMALIZATION = "SEMANTIC_NORMALIZATION"
    TECHNICAL_NEED = "TECHNICAL_NEED"
    ECONOMIC_DIMENSIONS = "ECONOMIC_DIMENSIONS"
    EVIDENCE_RETRIEVAL = "EVIDENCE_RETRIEVAL"
    COMPARABILITY = "COMPARABILITY"
    READINESS = "READINESS"
    RESPONSE = "RESPONSE"


class InputModality(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    TEXT_IMAGE = "TEXT+IMAGE"


class RealCaseClassification(str, Enum):
    REAL_CASE_ONLY = "REAL_CASE_ONLY"
    REGRESSION_CANDIDATE = "REGRESSION_CANDIDATE"
    GOLDEN_CANDIDATE = "GOLDEN_CANDIDATE"
    AMBIGUOUS_CASE = "AMBIGUOUS_CASE"
    UNRESOLVED_CASE = "UNRESOLVED_CASE"


class FailureType(str, Enum):
    PARSE_FAILURE = "PARSE_FAILURE"
    INTENT_FAILURE = "INTENT_FAILURE"
    SEMANTIC_MAPPING_FAILURE = "SEMANTIC_MAPPING_FAILURE"
    NORMALIZATION_FAILURE = "NORMALIZATION_FAILURE"
    CONTEXT_LOSS = "CONTEXT_LOSS"
    MISSING_USER_INFORMATION = "MISSING_USER_INFORMATION"
    MISSING_MARKET_EVIDENCE = "MISSING_MARKET_EVIDENCE"
    NON_COMPARABLE_EVIDENCE = "NON_COMPARABLE_EVIDENCE"
    WRONG_COMPARABILITY = "WRONG_COMPARABILITY"
    READINESS_FAILURE = "READINESS_FAILURE"
    UNSUPPORTED_DECISION = "UNSUPPORTED_DECISION"
    RESPONSE_EXPLANATION_FAILURE = "RESPONSE_EXPLANATION_FAILURE"
    PERFORMANCE_FAILURE = "PERFORMANCE_FAILURE"


@dataclass(frozen=True)
class StageTrace:
    stage: TraceStage
    status: str
    input_references: tuple[str, ...]
    output_references: tuple[str, ...]
    elapsed_ms: float
    unknowns_introduced: tuple[str, ...] = ()
    unknowns_resolved: tuple[str, ...] = ()
    ambiguities: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    failure_reason: str | None = None


@dataclass(frozen=True)
class NormalizationTrace:
    field: str
    raw_value: object
    normalized_value: object
    method: str
    status: str
    provenance: str


@dataclass(frozen=True)
class EvidenceDecisionTrace:
    evidence_id: str
    decision: str
    exclusion_reasons: tuple[str, ...]
    provenance: str


@dataclass(frozen=True)
class RealWorldQueryTrace:
    trace_id: str
    received_at: str | None
    source_case_id: str
    case_origin: str
    raw_user_input: str
    input_modality: InputModality
    request_context: dict
    parser_result: dict
    intent_result: dict
    technical_need_result: dict | None
    semantic_result: dict
    normalized_entities: tuple[NormalizationTrace, ...]
    economic_dimensions: dict
    unknown_dimensions: tuple[str, ...]
    ambiguities: tuple[str, ...]
    conflicts: tuple[str, ...]
    evidence_candidates: tuple[EvidenceDecisionTrace, ...]
    accepted_evidence: tuple[str, ...]
    excluded_evidence: tuple[str, ...]
    pair_cohort_state: dict
    readiness: str
    decision_state: str
    public_response: dict
    real_world_outcome: dict
    stages: tuple[StageTrace, ...]
    total_latency_ms: float
    trace_overhead_ms: float
    versions: dict
    provenance: tuple[str, ...]
    failures: tuple[FailureType, ...]
    classification: RealCaseClassification
    learning_yield: dict
    replay_fingerprint: str
    promotion_authorized: bool = False
    runtime_mutation: bool = False


def stable_trace_id(*, source_case_id: str, raw_user_input: str, case_origin: str) -> str:
    payload = json.dumps(
        {"case_origin": case_origin, "raw_user_input": raw_user_input, "source_case_id": source_case_id},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return "real-query-trace:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def replay_fingerprint(payload: dict) -> str:
    stable = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(stable.encode("utf-8")).hexdigest()
