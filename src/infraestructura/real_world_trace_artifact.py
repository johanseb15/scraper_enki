from __future__ import annotations

from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
from statistics import median

from src.aplicacion.pricing_cohort_loader import (
    cargar_cohortes_pricing,
    cargar_cohortes_pricing_runtime,
)
from src.dominio.real_world_query_trace import InputModality, TraceStage
from src.infraestructura.real_world_query_tracer import append_trace, build_learning_intake, trace_real_world_query


def build_real_world_trace_artifacts(root, output_dir):
    root, output = Path(root), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    corpus = _jsonl(root / "data/language/real_query_corpus_v1.jsonl")
    local, remote = cargar_cohortes_pricing_runtime()
    before_local = cargar_cohortes_pricing(
        root / "data/local_pricing_stats_lineage_v1.csv",
        require_runtime_lineage_gate=True,
    )
    before_remote = cargar_cohortes_pricing(
        root / "data/remote_pricing_stats_lineage_v1.csv",
        require_runtime_lineage_gate=True,
    )
    trace_path = output / "real_world_query_traces_v1.jsonl"
    intake_by_id = {}
    for record in corpus:
        trace = trace_real_world_query(
            record["query_raw"], local_cohortes=local, remote_cohortes=remote,
            source_case_id=record["id"], case_origin=record["provenance"],
            input_modality=InputModality.TEXT,
            provenance=(f"data/language/real_query_corpus_v1.jsonl#{record['id']}",),
            received_at=record.get("source_date"),
            request_context={"corpus_tags": record.get("tags", []), "provenance_status": record["provenance_status"]},
        )
        append_trace(trace_path, trace)
        intake = build_learning_intake(trace)
        regression_outcome, regression_errors = adjudicate_trace(record, trace)
        before_trace = trace_real_world_query(
            record["query_raw"],
            local_cohortes=before_local,
            remote_cohortes=before_remote,
            source_case_id=f"reach-before:{record['id']}",
            case_origin=record["provenance"],
        )
        before_outcome, before_errors = adjudicate_trace(record, before_trace)
        if (
            before_trace.readiness != trace.readiness
            and _semantic_projection(before_trace) == _semantic_projection(trace)
        ):
            if before_outcome == "WRONG_INTERPRETATION":
                regression_outcome, regression_errors = before_outcome, before_errors
            elif trace.readiness == "NO_EVIDENCE":
                regression_outcome, regression_errors = "EXPECTED_SAFETY_CHANGE", []
        intake["regression_outcome"] = regression_outcome
        intake["regression_errors"] = regression_errors
        intake_by_id[trace.trace_id] = intake

    persisted = _jsonl(trace_path)
    _write_jsonl(output / "real_world_learning_intake_v1.jsonl", (intake_by_id[key] for key in sorted(intake_by_id)))
    audit = _runtime_flow_audit()
    previous_audit = _csv(root / "data/language/real_query_audit_v1.csv")
    summary = _summary(persisted, tuple(intake_by_id.values()), previous_audit)
    _write_json(output / "real_world_runtime_flow_audit_v1.json", audit)
    _write_json(output / "real_world_performance_summary_v1.json", summary)
    return summary["metrics"]


def _runtime_flow_audit():
    rows = [
        _audit("INGEST", "DecisionPricingRequest.query", "raw_user_input", True, True, "LOW"),
        _audit("PARSE", "raw_user_input", "ParsedPricingQuery", True, True, "LOW"),
        _audit("INTENT", "ParsedPricingQuery", "IntentAction/IntentSide", True, True, "LOW"),
        _audit("SEMANTIC_NORMALIZATION", "raw_user_input", "canonical services/geography/price", True, True, "LOW"),
        _audit("TECHNICAL_NEED", "TechnicalNeed", "market resolution/evidence probe", True, True, "LOW"),
        _audit("ECONOMIC_DIMENSIONS", "ParsedPricingQuery", "runtime dimension projection", True, True, "NONE"),
        _audit("EVIDENCE_RETRIEVAL", "versioned pricing cohorts", "accepted/excluded cohort references", True, True, "NONE"),
        _audit("COMPARABILITY", "candidate cohort dimensions", "runtime comparable cohort state", True, True, "NONE"),
        _audit("READINESS", "EnkiPricingQueryResult", "DECISION/RANGE/INSUFFICIENT/etc", True, True, "NONE"),
        _audit("RESPONSE", "EnkiPricingQueryResult", "EnkiUserResponse", True, True, "NONE"),
    ]
    return {
        "schema_version": "real-world-runtime-flow-audit-v1",
        "public_entrypoint": "POST /decision/pricing",
        "runtime_path": "FastAPI -> resolver_consulta_pricing -> parser/TechnicalNeed/evidence -> presentar_resultado_pricing",
        "evidence_granularity": "AGGREGATED_PRICING_COHORT",
        "offer_level_runtime_evidence_available": False,
        "stages": rows,
        "runtime_mutation": False,
    }


def _audit(stage, input_name, output_name, provenance, uncertainty, risk):
    missing = {
        "EVIDENCE_RETRIEVAL": (
            "Gated cohorts expose constituent observation ids; global offer identity remains unavailable."
        ),
        "COMPARABILITY": "Runtime exposes selected aggregate cohort, not pair-level decisions.",
    }.get(stage)
    return {
        "stage": stage, "input": input_name, "output": output_name,
        "provenance_currently_available": provenance, "uncertainty_currently_available": uncertainty,
        "timing_possible": True, "missing_observability": missing, "runtime_mutation_risk": risk,
    }


def _summary(traces, intake, previous_audit):
    origins = Counter(item["case_origin"] for item in traces)
    readiness = Counter(item["readiness"] for item in traces)
    classifications = Counter(item["classification"] for item in traces)
    failures = Counter(failure for item in traces for failure in item["failures"])
    regression = Counter(item["regression_outcome"] for item in intake)
    failures_by_stage = Counter()
    response = Counter(item["public_response"]["headline"] for item in traces)
    stage_latencies = defaultdict(list)
    for item in traces:
        for stage in item["stages"]:
            stage_latencies[stage["stage"]].append(stage["elapsed_ms"])
            if stage["failure_reason"]:
                failures_by_stage[stage["stage"]] += 1
    totals = [item["total_latency_ms"] for item in traces]
    overhead = [item["trace_overhead_ms"] for item in traces]
    norm_num = sum(item["learning_yield"]["normalization_yield"]["numerator"] for item in traces)
    norm_den = sum(item["learning_yield"]["normalization_yield"]["denominator"] for item in traces)
    comp_num = sum(item["learning_yield"]["comparability_yield"]["numerator"] for item in traces)
    comp_den = sum(item["learning_yield"]["comparability_yield"]["denominator"] for item in traces)
    metrics = {
        "TOTAL_TRACES": len(traces), "TOTAL_REAL_TRACES": origins["HUMAN_REAL"],
        "TRACE_ORIGINS": dict(sorted(origins.items())),
        "SUCCESSFUL": len(traces) - regression["WRONG_INTERPRETATION"],
        "AMBIGUOUS": classifications["AMBIGUOUS_CASE"],
        "UNKNOWN_OR_UNRESOLVED": classifications["UNRESOLVED_CASE"],
        "WITH_COMPARABLE_EVIDENCE": sum(bool(item["accepted_evidence"]) for item in traces),
        "WITH_DECISION": readiness["DECISION_READY"],
        "READINESS_DISTRIBUTION": dict(sorted(readiness.items())),
        "RESPONSE_DISTRIBUTION": dict(sorted(response.items())),
        "FAILURE_TAXONOMY": dict(sorted(failures.items())),
        "REGRESSION_OUTCOMES": dict(sorted(regression.items())),
        "PREVIOUS_AUDIT_WRONG_INTERPRETATION": sum(item["audit_outcome"] == "WRONG_INTERPRETATION" for item in previous_audit),
        "CURRENT_AUDIT_WRONG_INTERPRETATION": regression["WRONG_INTERPRETATION"],
        "REGRESSION_AUDIT_DRIFT": regression["WRONG_INTERPRETATION"] - sum(item["audit_outcome"] == "WRONG_INTERPRETATION" for item in previous_audit),
        "PARSE_SUCCESSES": len(traces) - failures["PARSE_FAILURE"],
        "PARSE_FAILURES": failures["PARSE_FAILURE"],
        "INTENT_SUCCESSES": len(traces) - failures["INTENT_FAILURE"],
        "INTENT_FAILURES": failures["INTENT_FAILURE"],
        "NORMALIZATION_SUCCESSES": len(traces) - failures["NORMALIZATION_FAILURE"],
        "FAILURES_BY_STAGE": dict(sorted(failures_by_stage.items())),
        "NORMALIZATION_FAILURES": failures["NORMALIZATION_FAILURE"],
        "CONTEXT_FAILURES": failures["CONTEXT_LOSS"],
        "EVIDENCE_FAILURES": failures["MISSING_MARKET_EVIDENCE"],
        "COMPARABILITY_FAILURES": failures["NON_COMPARABLE_EVIDENCE"] + failures["WRONG_COMPARABILITY"],
        "NEW_GOLDEN_CANDIDATES": classifications["GOLDEN_CANDIDATE"],
        "NEW_KNOWLEDGE_CANDIDATES": 0,
        "LEARNING_INTAKE_CASES": sum(bool(item["failures"]) or item["regression_outcome"] == "WRONG_INTERPRETATION" for item in intake),
        "NEW_ACQUISITION_GAPS": failures["MISSING_MARKET_EVIDENCE"],
        "EVIDENCE_CANDIDATES": sum(len(item["evidence_candidates"]) for item in traces),
        "ACCEPTED_EVIDENCE": sum(len(item["accepted_evidence"]) for item in traces),
        "EXCLUDED_EVIDENCE": sum(len(item["excluded_evidence"]) for item in traces),
        "UNKNOWN_DIMENSIONS": sum(len(item["unknown_dimensions"]) for item in traces),
        "AMBIGUITIES_TOTAL": sum(len(item["ambiguities"]) for item in traces),
        "CONFLICTS_TOTAL": sum(len(item["conflicts"]) for item in traces),
        "CLAIMS_EXTRACTED": sum(item["learning_yield"]["claims_extracted"] for item in traces),
        "RAW_DOCUMENTS_USED": 0,
        "CLAIMS_PER_RAW": None,
        "REUSABLE_EVIDENCE_LINKS": sum(item["learning_yield"]["reusable_evidence_links"] for item in traces),
        "NORMALIZATION_YIELD": {"numerator": norm_num, "denominator": norm_den, "value": round(norm_num / norm_den, 6) if norm_den else None},
        "COMPARABILITY_YIELD": {"numerator": comp_num, "denominator": comp_den, "value": round(comp_num / comp_den, 6) if comp_den else None},
        "NETWORK_REQUESTS": 0, "AUTO_PROMOTIONS": 0, "RUNTIME_WRITES": 0,
    }
    performance = {
        "sample_size": len(traces), "sufficient_for_percentiles": len(traces) >= 20,
        "total_latency_ms": _distribution(totals) if len(traces) >= 20 else {"max": max(totals, default=None)},
        "trace_overhead_ms": _distribution(overhead) if len(traces) >= 20 else {"max": max(overhead, default=None)},
        "by_stage": {stage: _distribution(values) for stage, values in sorted(stage_latencies.items())},
    }
    return {"schema_version": "real-world-performance-summary-v1", "metrics": metrics, "performance": performance}


def adjudicate_trace(record, trace):
    adjudication = record["adjudication"]
    behavior = adjudication["expected_behavior"]
    errors = []
    expected_safety_change = False
    if behavior == "CLARIFICATION" and trace.readiness != "CLARIFICATION_REQUIRED":
        errors.append(f"expected CLARIFICATION_REQUIRED, got {trace.readiness}")
    if behavior == "SAFE_UNSUPPORTED" and trace.readiness != "UNSUPPORTED_QUERY":
        errors.append(f"expected UNSUPPORTED_QUERY, got {trace.readiness}")
    if behavior == "PARSE":
        if trace.readiness in {"CLARIFICATION_REQUIRED", "UNSUPPORTED_QUERY"}:
            errors.append(f"expected evidence path, got {trace.readiness}")
        expected_status = adjudication.get("expected_resolution_status")
        if expected_status and trace.readiness != expected_status:
            if (
                expected_status in {"RANGE_READY", "DECISION_READY"}
                and trace.readiness in {"INSUFFICIENT_EVIDENCE", "NO_EVIDENCE"}
            ):
                expected_safety_change = True
            else:
                errors.append(f"expected {expected_status}, got {trace.readiness}")
    actual = {
        "intent_action": trace.intent_result["action"], "intent_side": trace.intent_result["side"],
        "economic_object_kind": trace.parser_result["economic_object_kind"],
        "canonical_services": trace.parser_result["canonical_services"],
        "market_scope": trace.parser_result["market_scope"], "modality": trace.parser_result["modality"],
        "price_value": trace.parser_result["price"]["value"], "currency": trace.parser_result["price"]["currency"],
        "price_scope": trace.economic_dimensions["price_scope"]["value"],
        "province": trace.parser_result["geography"]["province"], "city": trace.parser_result["geography"]["city"],
    }
    for field, expected in adjudication.get("expected_fields", {}).items():
        if field in actual and actual[field] != expected:
            errors.append(f"{field}: expected={expected!r} actual={actual[field]!r}")
    if errors:
        return "WRONG_INTERPRETATION", errors
    if expected_safety_change:
        return "EXPECTED_SAFETY_CHANGE", []
    return {"CLARIFICATION": "CLARIFICATION_CORRECT", "SAFE_UNSUPPORTED": "SAFE_UNSUPPORTED", "PARSE": "PARSE_CORRECT"}[behavior], []


def _semantic_projection(trace):
    return {
        "intent": trace.intent_result,
        "parser": trace.parser_result,
        "economic_dimensions": trace.economic_dimensions,
        "technical_need": trace.technical_need_result,
        "semantic": trace.semantic_result,
    }


def _distribution(values):
    ordered = sorted(values)
    return {
        "p50": round(median(ordered), 6),
        "p95": round(ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)], 6),
        "max": round(max(ordered), 6),
    }


def _jsonl(path):
    path = Path(path)
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
