from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
import json
from pathlib import Path
from time import perf_counter_ns

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.enki_pricing_response import presentar_resultado_pricing
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_cohort_loader import DEFAULT_LOCAL_STATS, DEFAULT_REMOTE_STATS
from src.dominio.real_world_query_trace import (
    EvidenceDecisionTrace,
    FailureType,
    InputModality,
    NormalizationTrace,
    RealCaseClassification,
    RealWorldQueryTrace,
    StageTrace,
    TraceStage,
    replay_fingerprint,
    stable_trace_id,
)
from src.dominio.commercial_context import (
    CommercialContextCompatibility,
    compare_commercial_contexts,
    serialize_commercial_context,
)


TRACE_VERSION = "real-world-query-trace-v1"
PARSER_VERSION = "pricing-query-parser-v1"
RUNTIME_VERSION = "enki-decision-runtime-v1"


def trace_real_world_query(
    raw_user_input,
    *,
    local_cohortes,
    remote_cohortes,
    source_case_id,
    case_origin,
    input_modality=InputModality.TEXT,
    provenance=(),
    received_at=None,
    request_context=None,
):
    total_start = perf_counter_ns()
    stages = []

    value, elapsed = _measure(lambda: {
        "raw_length": len(raw_user_input), "modality": input_modality.value,
        "supported": input_modality is InputModality.TEXT,
    })
    stages.append(_stage(TraceStage.INGEST, "OK" if value["supported"] else "UNSUPPORTED", elapsed, ("request",), ("raw_user_input",),
                         failure=None if value["supported"] else "MISSING_CAPABILITY"))
    if input_modality is not InputModality.TEXT:
        raise ValueError("Runtime v1 supports TEXT tracing only; unsupported modalities must not be parsed.")

    parsed, parse_ms = _measure(lambda: parse_pricing_query(raw_user_input, language_evidence_type=case_origin))
    parser_unknowns = _parser_unknowns(parsed)
    stages.append(_stage(TraceStage.PARSE, "OK", parse_ms, ("raw_user_input",), ("parsed_query",), unknowns=parser_unknowns,
                         ambiguities=_ambiguities(parsed)))

    intent, intent_ms = _measure(lambda: {"action": parsed.intent_action.value, "side": parsed.intent_side.value})
    stages.append(_stage(TraceStage.INTENT, "UNKNOWN" if parsed.intent_action.value == "UNKNOWN" else "OK", intent_ms,
                         ("parsed_query",), ("intent_result",), unknowns=("intent_action",) if parsed.intent_action.value == "UNKNOWN" else ()))

    normalized, normalization_ms = _measure(lambda: _normalizations(parsed))
    stages.append(_stage(TraceStage.SEMANTIC_NORMALIZATION, "PARTIAL" if parser_unknowns else "OK", normalization_ms,
                         ("parsed_query",), tuple(item.field for item in normalized), unknowns=parser_unknowns,
                         ambiguities=_ambiguities(parsed)))

    technical, technical_ms = _measure(lambda: _technical_projection(parsed))
    stages.append(_stage(TraceStage.TECHNICAL_NEED, "OK" if technical else "NOT_APPLICABLE", technical_ms,
                         ("parsed_query",), ("technical_need",) if technical else ()))

    economic, economic_ms = _measure(lambda: _economic_dimensions(parsed))
    unknown_dimensions = tuple(sorted(key for key, item in economic.items() if item["status"] == "UNKNOWN"))
    stages.append(_stage(TraceStage.ECONOMIC_DIMENSIONS, "PARTIAL" if unknown_dimensions else "OK", economic_ms,
                         ("parsed_query",), tuple(economic), unknowns=unknown_dimensions))

    decision_start = perf_counter_ns()
    result = resolver_consulta_pricing(
        raw_user_input, local_cohortes=local_cohortes, remote_cohortes=remote_cohortes,
        language_evidence_type=case_origin, parsed_query=parsed,
    )
    decision_ms = _ms(decision_start)
    evidence_candidates, accepted, excluded = _evidence_projection(parsed, result, tuple(local_cohortes), tuple(remote_cohortes))
    stages.append(_stage(TraceStage.EVIDENCE_RETRIEVAL, "FOUND" if accepted else "NONE", decision_ms,
                         ("economic_dimensions", "pricing_cohorts"), tuple(item.evidence_id for item in evidence_candidates),
                         failure=None if accepted else "NO_ACCEPTED_RUNTIME_COHORT"))

    pair_cohort, comparability_ms = _measure(lambda: _pair_cohort_state(result, evidence_candidates))
    stages.append(_stage(TraceStage.COMPARABILITY, pair_cohort["status"], comparability_ms,
                         tuple(item.evidence_id for item in evidence_candidates), tuple(accepted),
                         failure=pair_cohort.get("reason")))

    readiness, readiness_ms = _measure(lambda: result.status)
    stages.append(_stage(TraceStage.READINESS, readiness, readiness_ms, ("runtime_result",), ("readiness",),
                         failure=result.clarification_reason or result.unsupported_reason))

    response, response_ms = _measure(lambda: asdict(presentar_resultado_pricing(result)))
    stages.append(_stage(TraceStage.RESPONSE, "OK", response_ms, ("runtime_result",), ("public_response",)))

    failures = _failures(parsed, result, accepted)
    classification = _classification(parsed, result, case_origin)
    conflicts = _conflicts(parsed)
    ambiguities = _ambiguities(parsed)
    learning_yield = _learning_yield(normalized, unknown_dimensions, ambiguities, conflicts, evidence_candidates, accepted, failures)
    parser_result = _parser_payload(parsed)
    semantic = {
        "canonical_services": list(parsed.canonical_services), "economic_object_kind": parsed.economic_object_kind.value,
        "query_kind": parsed.query_kind.value, "confidence": parsed.metadata.confidence,
    }
    stable_payload = {
        "raw_user_input": raw_user_input, "parser_result": parser_result, "intent_result": intent,
        "technical_need_result": technical, "semantic_result": semantic, "economic_dimensions": economic,
        "unknown_dimensions": unknown_dimensions, "evidence": [_json_value(asdict(item)) for item in evidence_candidates],
        "readiness": readiness, "public_response": response, "failures": [item.value for item in failures],
        "versions": {"trace": TRACE_VERSION, "parser": PARSER_VERSION, "runtime": RUNTIME_VERSION},
    }
    overhead_ms = sum(item.elapsed_ms for item in stages if item.stage not in {TraceStage.PARSE, TraceStage.EVIDENCE_RETRIEVAL})
    return RealWorldQueryTrace(
        trace_id=stable_trace_id(source_case_id=source_case_id, raw_user_input=raw_user_input, case_origin=case_origin),
        received_at=received_at, source_case_id=source_case_id, case_origin=case_origin,
        raw_user_input=raw_user_input, input_modality=input_modality, request_context=request_context or {},
        parser_result=parser_result, intent_result=intent, technical_need_result=technical,
        semantic_result=semantic, normalized_entities=normalized, economic_dimensions=economic,
        unknown_dimensions=unknown_dimensions, ambiguities=ambiguities, conflicts=conflicts,
        evidence_candidates=evidence_candidates, accepted_evidence=accepted, excluded_evidence=excluded,
        pair_cohort_state=pair_cohort, readiness=readiness,
        decision_state=result.decision_label or readiness, public_response=response,
        real_world_outcome={"status": "UNKNOWN", "feedback": None}, stages=tuple(stages),
        total_latency_ms=round(_ms(total_start), 6), trace_overhead_ms=round(overhead_ms, 6),
        versions={"trace": TRACE_VERSION, "parser": PARSER_VERSION, "runtime": RUNTIME_VERSION},
        provenance=tuple(provenance), failures=failures, classification=classification,
        learning_yield=learning_yield, replay_fingerprint=replay_fingerprint(stable_payload),
    )


def append_trace(path, trace):
    path = Path(path)
    rows = _jsonl(path)
    payload = {"schema_version": TRACE_VERSION, **_json_value(asdict(trace))}
    existing = next((item for item in rows if item["trace_id"] == trace.trace_id), None)
    if existing and existing["replay_fingerprint"] != trace.replay_fingerprint:
        raise ValueError("Trace id collision with a different replay fingerprint.")
    if existing is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def build_learning_intake(trace):
    gap_types = []
    if FailureType.MISSING_MARKET_EVIDENCE in trace.failures:
        gap_types.append("ACQUISITION_GAP")
    if FailureType.NON_COMPARABLE_EVIDENCE in trace.failures:
        gap_types.append("ECONOMIC_EVIDENCE_GAP")
    if FailureType.NORMALIZATION_FAILURE in trace.failures or FailureType.SEMANTIC_MAPPING_FAILURE in trace.failures:
        gap_types.append("NORMALIZATION_REGRESSION")
    return {
        "schema_version": "real-world-learning-intake-v1", "trace_id": trace.trace_id,
        "source_case_id": trace.source_case_id,
        "case_origin": trace.case_origin, "classification": trace.classification.value,
        "failures": [item.value for item in trace.failures], "gap_types": gap_types,
        "candidate_status": "CANDIDATE_ONLY", "promotion_authorized": False,
        "suggested_next_evidence": _suggested_next_evidence(trace),
    }


def _stage(stage, status, elapsed, inputs, outputs, *, unknowns=(), ambiguities=(), failure=None):
    return StageTrace(stage, status, tuple(inputs), tuple(outputs), round(elapsed, 6), tuple(unknowns), (), tuple(ambiguities), (), failure)


def _measure(function):
    started = perf_counter_ns(); value = function(); return value, _ms(started)


def _ms(started):
    return (perf_counter_ns() - started) / 1_000_000


def _parser_unknowns(parsed):
    values = {
        "intent_action": parsed.intent_action.value, "intent_side": parsed.intent_side.value,
        "economic_object_kind": parsed.economic_object_kind.value, "market_scope": parsed.market_scope.value,
        "modality": parsed.modality.value, "price.currency": parsed.price.currency,
        "price.type": parsed.price.type.value, "geography.province": parsed.geography.province or "UNKNOWN",
        "device.condition": parsed.condition, "parts_scope": parsed.commercial_context.parts_scope.value,
    }
    return tuple(sorted(key for key, value in values.items() if value == "UNKNOWN"))


def _ambiguities(parsed):
    reason = parsed.metadata.clarification_reason or ""
    return tuple(sorted(part for part in reason.split("|") if part in {"MULTIPLE_MONETARY_MENTIONS", "BUNDLE_REQUIRES_COMPARABLE_SCOPE"}))


def _conflicts(parsed):
    return ()  # Runtime v1 exposes no typed conflict collection; absence is not inferred resolution.


def _normalizations(parsed):
    items = [NormalizationTrace("query.normalized_text", parsed.raw_text, parsed.normalized_text, "UNICODE_FOLD", "INFERRED", "raw_user_input")]
    if parsed.price.value is not None:
        items.append(NormalizationTrace("price.value", parsed.price.raw_expression, parsed.price.value, "PRICE_PARSER", "OBSERVED", "raw_user_input"))
    if parsed.price.currency != "UNKNOWN":
        items.append(NormalizationTrace("price.currency", parsed.price.raw_expression, parsed.price.currency, "CURRENCY_PARSER", "INFERRED", "raw_user_input"))
    if parsed.canonical_services:
        items.append(NormalizationTrace("canonical_services", parsed.raw_text, list(parsed.canonical_services), "SEMANTIC_LEXICON", "DERIVED", "raw_user_input"))
    if parsed.geography.raw_location:
        items.append(NormalizationTrace("geography", parsed.geography.raw_location, {"province": parsed.geography.province, "city": parsed.geography.city}, "GEOGRAPHY_NORMALIZER", "INFERRED", "raw_user_input"))
    if parsed.modality.value != "UNKNOWN":
        items.append(NormalizationTrace("modality", parsed.raw_text, parsed.modality.value, "CONTEXT_PATTERN", "DERIVED", "raw_user_input"))
    return tuple(items)


def _technical_projection(parsed):
    return None if parsed.technical_need is None else _json_value(asdict(parsed.technical_need))


def _economic_dimensions(parsed):
    price_scope = parsed.price_scope.comparison_scope
    values = {
        "economic_object_kind": parsed.economic_object_kind.value,
        "service": list(parsed.canonical_services) or None,
        "market_scope": parsed.market_scope.value,
        "location": {"province": parsed.geography.province, "city": parsed.geography.city} if parsed.geography.province else None,
        "delivery_mode": parsed.modality.value,
        "price": parsed.price.value,
        "currency": parsed.price.currency,
        "price_scope": price_scope,
        "charged_unit": parsed.price_scope.charged_unit.value,
        "billing_period": parsed.price_scope.billing_period.value,
        "price_bound": parsed.price_scope.price_bound.value,
        "device": parsed.device_type,
        "hardware_included": None,
        "materials_included": None,
        "bundle": parsed.is_bundle,
    }
    dimensions = {key: {"value": value, "status": "UNKNOWN" if value is None or value == "UNKNOWN" else "OBSERVED" if key in {"price", "location"} else "INFERRED", "provenance": "parsed_query"} for key, value in values.items()}
    context = serialize_commercial_context(parsed.commercial_context)
    dimensions["commercial_context"] = {
        "value": context["value"],
        "status": context["status"],
        "provenance": context["origin"],
        "raw_basis": context["raw_basis"],
        "resolution_method": context["resolution_method"],
    }
    return dimensions


def _cohort_id(item):
    return item.evidence_id


def _engine_selected_evidence_ids(result):
    selected = set()
    if result.evidence and result.evidence.evidence_id:
        selected.add(result.evidence.evidence_id)
    if result.evidence_probe:
        selected.update(
            item.evidence_id
            for item in result.evidence_probe.probes
            if item.evidence_id
        )
    return selected


def _evidence_projection(parsed, result, local, remote):
    cohorts = remote if parsed.market_scope.value == "REMOTE_NATIONAL" else local if parsed.market_scope.value == "LOCAL" else local + remote
    targets = set(parsed.canonical_services)
    if result.market_resolution:
        targets |= {item.canonical_service for item in result.market_resolution.resolutions if item.canonical_service}
    expected_market = "AR" if parsed.market_scope.value == "REMOTE_NATIONAL" else parsed.geography.province
    price_scope = result.evidence.price_scope if result.evidence else parsed.price_scope.comparison_scope
    commercial_context = parsed.commercial_context
    selected_ids = _engine_selected_evidence_ids(result)
    candidates = []
    for item in cohorts:
        if not targets or item.canonical_service not in targets:
            continue
        reasons = []
        if expected_market and item.market != expected_market: reasons.append("MARKET_MISMATCH")
        if not result.market_resolution and item.price_scope != price_scope:
            reasons.append("PRICE_SCOPE_UNKNOWN_SIDE" if "UNKNOWN" in {item.price_scope, price_scope} else "PRICE_SCOPE_MISMATCH")
        if not result.market_resolution:
            context_compatibility = compare_commercial_contexts(
                item.commercial_context,
                commercial_context,
            )
            if context_compatibility is CommercialContextCompatibility.MISMATCH:
                reasons.append("COMMERCIAL_CONTEXT_MISMATCH")
            elif context_compatibility is CommercialContextCompatibility.UNKNOWN_SIDE:
                reasons.append("COMMERCIAL_CONTEXT_UNKNOWN_SIDE")
            elif context_compatibility is CommercialContextCompatibility.AMBIGUOUS_SIDE:
                reasons.append("COMMERCIAL_CONTEXT_AMBIGUOUS_SIDE")
        accepted = _cohort_id(item) in selected_ids
        candidates.append(EvidenceDecisionTrace(
            _cohort_id(item), "ACCEPTED" if accepted else "EXCLUDED", tuple(reasons or (() if accepted else ("NOT_SELECTED_BY_RUNTIME",))),
            DEFAULT_LOCAL_STATS.as_posix() if item in local else DEFAULT_REMOTE_STATS.as_posix(),
        ))
    accepted_ids = tuple(item.evidence_id for item in candidates if item.decision == "ACCEPTED")
    excluded_ids = tuple(item.evidence_id for item in candidates if item.decision == "EXCLUDED")
    return tuple(candidates), accepted_ids, excluded_ids


def _pair_cohort_state(result, candidates):
    accepted = sum(item.decision == "ACCEPTED" for item in candidates)
    status = "READY" if result.status == "DECISION_READY" else "PARTIAL" if result.status in {"RANGE_READY", "INSUFFICIENT_EVIDENCE", "TECHNICAL_NEED_ROUTED"} else "INSUFFICIENT"
    return {"status": status, "accepted_cohorts": accepted, "candidate_cohorts": len(candidates), "reason": None if accepted else "NO_COMPARABLE_RUNTIME_COHORT"}


def _failures(parsed, result, accepted):
    failures = set()
    if parsed.economic_object_kind.value == "UNKNOWN": failures.add(FailureType.SEMANTIC_MAPPING_FAILURE)
    if parsed.intent_action.value == "UNKNOWN": failures.add(FailureType.INTENT_FAILURE)
    if parsed.metadata.clarification_required: failures.add(FailureType.MISSING_USER_INFORMATION)
    if not accepted and result.status in {"NO_EVIDENCE", "TECHNICAL_NEED_ROUTED"}: failures.add(FailureType.MISSING_MARKET_EVIDENCE)
    if result.status == "INSUFFICIENT_EVIDENCE": failures.add(FailureType.NON_COMPARABLE_EVIDENCE)
    if result.status == "UNSUPPORTED_QUERY": failures.add(FailureType.READINESS_FAILURE)
    return tuple(sorted(failures, key=lambda item: item.value))


def _classification(parsed, result, origin):
    if parsed.metadata.clarification_required: return RealCaseClassification.AMBIGUOUS_CASE
    if result.status in {"UNSUPPORTED_QUERY", "NO_EVIDENCE"}: return RealCaseClassification.UNRESOLVED_CASE
    if origin == "HUMAN_REAL": return RealCaseClassification.REAL_CASE_ONLY
    return RealCaseClassification.REGRESSION_CANDIDATE


def _learning_yield(normalized, unknowns, ambiguities, conflicts, candidates, accepted, failures):
    normalized_n, unknown_n = len(normalized), len(unknowns)
    return {
        "raw_documents_used": 0, "offers_identified": 0,
        "claims_extracted": normalized_n + len(accepted), "normalized_claims": normalized_n,
        "unknown_claims": unknown_n, "ambiguities": len(ambiguities), "conflicts": len(conflicts),
        "candidate_opportunities": len(failures), "evidence_gaps": sum(item in failures for item in {FailureType.MISSING_MARKET_EVIDENCE, FailureType.NON_COMPARABLE_EVIDENCE}),
        "reusable_evidence_links": len(accepted),
        "normalization_yield": {"numerator": normalized_n, "denominator": normalized_n + unknown_n, "value": round(normalized_n / (normalized_n + unknown_n), 6) if normalized_n + unknown_n else None},
        "comparability_yield": {"numerator": len(accepted), "denominator": len(candidates), "value": round(len(accepted) / len(candidates), 6) if candidates else None},
        "claims_per_raw": None, "network_requests": 0,
    }


def _parser_payload(parsed):
    return {
        "raw_text": parsed.raw_text, "normalized_text": parsed.normalized_text,
        "query_kind": parsed.query_kind.value, "economic_object_kind": parsed.economic_object_kind.value,
        "canonical_services": list(parsed.canonical_services), "market_scope": parsed.market_scope.value,
        "modality": parsed.modality.value, "price": _json_value(asdict(parsed.price)),
        "geography": _json_value(asdict(parsed.geography)), "clarification_required": parsed.metadata.clarification_required,
        "clarification_reason": parsed.metadata.clarification_reason,
        "price_scope": _json_value(asdict(parsed.price_scope)),
        "commercial_context": serialize_commercial_context(parsed.commercial_context),
    }


def _suggested_next_evidence(trace):
    if FailureType.MISSING_USER_INFORMATION in trace.failures: return "REQUEST_EXACT_MISSING_CONTEXT"
    if FailureType.MISSING_MARKET_EVIDENCE in trace.failures: return "TARGET_MATCHING_MARKET_AND_SERVICE_COHORT"
    if FailureType.NON_COMPARABLE_EVIDENCE in trace.failures: return "DENSIFY_INDEPENDENT_COMPARABLE_PROVIDERS"
    return "REVIEW_REAL_CASE_WITHOUT_PROMOTION"


def _jsonl(path):
    path = Path(path)
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _json_value(value):
    if isinstance(value, dict): return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [_json_value(item) for item in value]
    if isinstance(value, Decimal): return float(value)
    if hasattr(value, "value") and hasattr(value, "name"): return value.value
    return value
