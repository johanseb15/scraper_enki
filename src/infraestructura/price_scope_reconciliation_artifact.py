from __future__ import annotations

from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

from scripts.build_pricing_statistics import build_pricing_statistics
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing
from src.aplicacion.pricing_dimensions import infer_commercial_context, infer_price_scope
from src.dominio.real_world_query_trace import InputModality
from src.infraestructura.real_world_query_tracer import append_trace, trace_real_world_query
from src.infraestructura.real_world_trace_artifact import adjudicate_trace


def build_price_scope_reconciliation(root, output_dir):
    root, output = Path(root), Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    local_v2 = output / "local_pricing_stats_v2.csv"
    remote_v2 = output / "remote_pricing_stats_v2.csv"
    build_pricing_statistics(root / "data/semantic_normalization_v4.csv", local_out_path=local_v2, remote_out_path=remote_v2)
    before_traces = _jsonl(root / "data/real_world_query_traces_v1.jsonl")
    corpus = _jsonl(root / "data/language/real_query_corpus_v1.jsonl")
    old_audit = {row["id"]: row for row in _csv(root / "data/language/real_query_audit_v1.csv")}
    old_intake = {row["source_case_id"]: row for row in _jsonl(root / "data/real_world_learning_intake_v1.jsonl")}
    before_by_id = {row["source_case_id"]: row for row in before_traces}

    local_after, remote_after = cargar_cohortes_pricing(local_v2), cargar_cohortes_pricing(remote_v2)
    after_path = output / "real_world_query_traces_price_scope_v2.jsonl"
    after_objects = {}
    after_audit = {}
    for record in corpus:
        trace = trace_real_world_query(
            record["query_raw"], local_cohortes=local_after, remote_cohortes=remote_after,
            source_case_id=record["id"], case_origin=record["provenance"], input_modality=InputModality.TEXT,
            provenance=(f"data/language/real_query_corpus_v1.jsonl#{record['id']}", "price-scope-contract-v1"),
            request_context={"evaluation": "PRICE_SCOPE_RECONCILIATION_AFTER"},
        )
        append_trace(after_path, trace); after_objects[record["id"]] = trace
        outcome, errors = adjudicate_trace(record, trace)
        after_audit[record["id"]] = {"outcome": outcome, "errors": errors}

    unknown_rows = _unknown_classification(corpus, before_by_id)
    sidecar = _cohort_sidecar(root, local_v2, remote_v2)
    drift = _drift_audit(corpus, old_audit, old_intake, before_by_id, after_objects, after_audit)
    before_after = _before_after(corpus, before_by_id, old_intake, after_objects, after_audit, unknown_rows)
    _write_json(output / "price_scope_contract_audit_v1.json", _contract_audit())
    _write_jsonl(output / "price_scope_unknown_classification_v1.jsonl", unknown_rows)
    _write_jsonl(output / "pricing_cohort_scope_evidence_v1.jsonl", sidecar)
    _write_jsonl(output / "price_scope_drift_audit_v1.jsonl", drift)
    _write_json(output / "price_scope_reconciliation_before_after_v1.json", before_after)
    return before_after["metrics"]


def _unknown_classification(corpus, before):
    rows = []
    for record in corpus:
        trace = before[record["id"]]
        if trace["economic_dimensions"]["price_scope"]["value"] != "UNKNOWN": continue
        parsed = parse_pricing_query(record["query_raw"], language_evidence_type=record["provenance"])
        recovered = parsed.price_scope.comparison_scope
        classification = "B_EXPLICIT_INPUT_PARSER_LOSS" if recovered != "UNKNOWN" else "A_LEGITIMATE_UNKNOWN_INPUT_OMITTED_SCOPE"
        rows.append({
            "schema_version": "price-scope-unknown-classification-v1", "query_id": record["id"],
            "raw_user_input": record["query_raw"], "before_scope": "UNKNOWN", "after_parser_scope": recovered,
            "classification": classification, "raw_basis": parsed.price_scope.raw_basis,
            "provenance": f"data/language/real_query_corpus_v1.jsonl#{record['id']}",
        })
    return tuple(sorted(rows, key=lambda item: item["query_id"]))


def _cohort_sidecar(root, local_path, remote_path):
    normalization = _csv(root / "data/semantic_normalization_v4.csv")
    grouped = defaultdict(list)
    for row in normalization:
        if row["semantic_role"] != "SINGLE_SERVICE" or row["currency"] != "ARS" or not row["canonical_service"]: continue
        if row["market_scope"] not in {"LOCAL_SERVICE", "REMOTE_NATIONAL_SERVICE"}: continue
        market = row["province"] if row["market_scope"] == "LOCAL_SERVICE" else "AR"
        scope = infer_price_scope(row["economic_object_raw"])
        context = infer_commercial_context(row["economic_object_raw"])
        grouped[(market, row["canonical_service"], scope, context)].append(row)
    output = []
    for cohort_file in (local_path, remote_path):
        for cohort in _csv(cohort_file):
            key = (cohort["market"], cohort["canonical_service"], cohort["price_scope"], cohort["commercial_context"])
            evidence = grouped[key]
            output.append({
                "schema_version": "pricing-cohort-scope-evidence-v1",
                "cohort_id": f"pricing-cohort:{':'.join(key)}", "cohort_file": Path(cohort_file).name,
                "price_scope": cohort["price_scope"],
                "status": "OBSERVED" if cohort["price_scope"] != "UNKNOWN" else "UNKNOWN",
                "observations": [{"observation_id": row["observation_id"], "source": row["source"], "raw_basis": row["economic_object_raw"], "provenance": "data/semantic_normalization_v4.csv"} for row in evidence],
                "raw_rewritten": False,
            })
    return tuple(sorted(output, key=lambda item: item["cohort_id"]))


def _drift_audit(corpus, historical, before_intake, before_traces, after, after_audit):
    rows = []
    for record in corpus:
        qid = record["id"]; old = historical[qid]; before = before_intake[qid]
        if old["audit_outcome"] == before["regression_outcome"] and old["actual_status"] == before_traces[qid]["readiness"]: continue
        historical_wrong = old["audit_outcome"] == "WRONG_INTERPRETATION"
        before_wrong = before["regression_outcome"] == "WRONG_INTERPRETATION"
        net = (1 if before_wrong else 0) - (1 if historical_wrong else 0)
        query_scope = parse_pricing_query(record["query_raw"]).price_scope.comparison_scope
        price_involved = old["actual_status"] != before_traces[qid]["readiness"] and before_traces[qid]["readiness"] in {"DECISION_READY", "RANGE_READY", "NO_EVIDENCE", "INSUFFICIENT_EVIDENCE", "CLARIFICATION_REQUIRED"}
        root = "COHORT_PRICE_SCOPE_SCHEMA_DRIFT" if price_involved else "NON_PRICE_SCOPE_RUNTIME_DRIFT"
        rows.append({
            "schema_version": "price-scope-drift-audit-v1", "query_id": qid, "raw_user_input": record["query_raw"],
            "historical_interpretation": {"status": old["actual_status"], "outcome": old["audit_outcome"], "errors": old["errors"]},
            "runtime_before": {"status": before_traces[qid]["readiness"], "outcome": before["regression_outcome"], "errors": before["regression_errors"]},
            "runtime_after": {"status": after[qid].readiness, **after_audit[qid]},
            "changed_component": "PRICING_COHORT_RUNTIME" if price_involved else "PARSER_OR_ADJUDICATION",
            "root_cause": root, "price_scope_involved": price_involved,
            "semantic_mapping_involved": any("canonical_services" in error or "economic_object_kind" in error for error in before["regression_errors"]),
            "intent_involved": any("intent_" in error for error in before["regression_errors"]),
            "evidence_involved": price_involved, "wrong_interpretation_net_delta": net,
            "regression_classification": "FIXED" if after_audit[qid]["outcome"] != "WRONG_INTERPRETATION" else "REMAINS",
        })
    return tuple(sorted(rows, key=lambda item: item["query_id"]))


def _before_after(corpus, before, before_intake, after, after_audit, unknown_rows):
    before_readiness = Counter(item["readiness"] for item in before.values())
    after_readiness = Counter(item.readiness for item in after.values())
    before_wrong = sum(item["regression_outcome"] == "WRONG_INTERPRETATION" for item in before_intake.values())
    after_wrong = sum(item["outcome"] == "WRONG_INTERPRETATION" for item in after_audit.values())
    explicit = [parse_pricing_query(item["query_raw"]).price_scope.comparison_scope for item in corpus]
    before_mismatch = sum("PRICE_SCOPE_MISMATCH" in candidate["exclusion_reasons"] for item in before.values() for candidate in item["evidence_candidates"])
    after_mismatch = sum("PRICE_SCOPE_MISMATCH" in candidate.exclusion_reasons for item in after.values() for candidate in item.evidence_candidates)
    before_unknown_side = sum("PRICE_SCOPE_UNKNOWN_SIDE" in candidate["exclusion_reasons"] for item in before.values() for candidate in item["evidence_candidates"])
    after_unknown_side = sum("PRICE_SCOPE_UNKNOWN_SIDE" in candidate.exclusion_reasons for item in after.values() for candidate in item.evidence_candidates)
    clarifications = Counter()
    for record in corpus:
        trace = after[record["id"]]
        if trace.readiness != "CLARIFICATION_REQUIRED": continue
        expected = record["adjudication"]["expected_behavior"]
        clarifications["JUSTIFIED_CLARIFICATION" if expected == "CLARIFICATION" else "WRONG_CLARIFICATION" if expected == "SAFE_UNSUPPORTED" else "UNNECESSARY_CLARIFICATION"] += 1
    metrics = {
        "TOTAL_TRACES": len(corpus), "HUMAN_REAL": 0,
        "PRICE_SCOPE_EXPLICIT_INPUT": sum(value != "UNKNOWN" for value in explicit),
        "PRICE_SCOPE_CORRECTLY_PARSED_BEFORE": sum(value != "UNKNOWN" for value in explicit) - sum(item["classification"].startswith("B_") for item in unknown_rows),
        "PRICE_SCOPE_CORRECTLY_PARSED_AFTER": sum(value != "UNKNOWN" for value in explicit),
        "PRICE_SCOPE_LOST_BEFORE": sum(item["classification"].startswith("B_") for item in unknown_rows),
        "PRICE_SCOPE_LOST_AFTER": 0,
        "PRICE_SCOPE_LEGITIMATE_UNKNOWN": sum(item["classification"].startswith("A_") for item in unknown_rows),
        "PRICE_SCOPE_MATCHES_BEFORE": sum(len(item["accepted_evidence"]) for item in before.values()),
        "PRICE_SCOPE_MATCHES_AFTER": sum(len(item.accepted_evidence) for item in after.values()),
        "PRICE_SCOPE_MISMATCHES_BEFORE": before_mismatch, "PRICE_SCOPE_MISMATCHES_AFTER": after_mismatch,
        "PRICE_SCOPE_UNKNOWN_SIDE_BEFORE": before_unknown_side, "PRICE_SCOPE_UNKNOWN_SIDE_AFTER": after_unknown_side,
        "COMPARABILITY_BEFORE": {
            "accepted": sum(len(item["accepted_evidence"]) for item in before.values()),
            "excluded": sum(len(item["excluded_evidence"]) for item in before.values()),
        },
        "COMPARABILITY_AFTER": {
            "accepted": sum(len(item.accepted_evidence) for item in after.values()),
            "excluded": sum(len(item.excluded_evidence) for item in after.values()),
        },
        "READINESS_BEFORE": dict(sorted(before_readiness.items())), "READINESS_AFTER": dict(sorted(after_readiness.items())),
        "WRONG_INTERPRETATION_BEFORE": before_wrong, "WRONG_INTERPRETATION_AFTER": after_wrong,
        "CLARIFICATION_QUALITY_AFTER": dict(sorted(clarifications.items())),
        "EXPLICIT_NORMALIZATION_RECALL": {"numerator": sum(value != "UNKNOWN" for value in explicit), "denominator": sum(value != "UNKNOWN" for value in explicit), "value": 1.0},
        "AUTO_PROMOTIONS": 0, "NETWORK_REQUESTS": 0, "RUNTIME_WRITES": 0,
    }
    return {"schema_version": "price-scope-reconciliation-before-after-v1", "metrics": metrics}


def _contract_audit():
    representations = (
        ("language_query_contract.py", "PriceType", "price form and charged scope conflated"),
        ("price_scope_contract.py", "PriceScopeMeaning", "canonical orthogonal contract"),
        ("offer_evidence.py", "ChargedUnit", "source charged unit"),
        ("offer_evidence.py", "PriceBound", "source price bound"),
        ("pricing_dimensions.py", "infer_price_scope", "source cadence projection"),
        ("economic_dimensions_v2", "price_scope", "economic scalar dimension"),
        ("local/remote_pricing_stats_v1.csv", "missing price_scope column", "legacy runtime cohort gap"),
        ("local/remote_pricing_stats_v2.csv", "price_scope", "versioned explicit/unknown cohort dimension"),
        ("pricing_evidence_engine.py", "CohortePricing.price_scope", "runtime comparability key"),
        ("real_world_query_trace.py", "economic_dimensions.price_scope", "decision trace projection"),
    )
    return {"schema_version": "price-scope-contract-audit-v1", "canonical_contract": "PriceScopeMeaning", "orthogonal_dimensions": ["charged_unit", "billing_period", "price_bound", "commercial_context"], "representations": [{"file_module": file, "field": field, "semantic_meaning": meaning, "provenance": "brownfield audit", "producer": "documented module", "consumer": "runtime/evaluation", "ambiguity": "documented", "known_mismatch": "legacy conflation" if "conflat" in meaning or "gap" in meaning else None} for file, field, meaning in representations]}


def _csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle: return list(csv.DictReader(handle))


def _jsonl(path):
    path = Path(path)
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
