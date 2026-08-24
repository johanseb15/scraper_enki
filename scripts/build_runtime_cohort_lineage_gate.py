from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from scripts.audit_real_query_corpus import classify
from scripts.build_pricing_statistics import build_runtime_pricing_statistics
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing
from src.aplicacion.pricing_dimensions import infer_commercial_context, infer_price_scope
from src.infraestructura.offer_evidence_artifact import load_offer_evidence_sidecar
from src.infraestructura.real_world_query_tracer import trace_real_world_query


SCHEMA_VERSION = "runtime-cohort-lineage-gate-v1"
START_HEAD = "1d10f977cbccc07250506ad6bd02deb631bf3e8d"


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _semantic_projection(trace) -> dict[str, object]:
    return {
        "parser_result": trace.parser_result,
        "intent_result": trace.intent_result,
        "semantic_result": trace.semantic_result,
        "economic_dimensions": trace.economic_dimensions,
    }


def _cohort_id(row: dict[str, str]) -> str:
    market = row["province"] if row["market_scope"] == "LOCAL_SERVICE" else "AR"
    return (
        f"pricing-cohort:{market}:{row['canonical_service'].strip()}:"
        f"{infer_price_scope(row.get('economic_object_raw', ''))}:"
        f"{infer_commercial_context(row.get('economic_object_raw', '')).value.value}"
    )


def _cohort_payload(cohort) -> dict[str, object]:
    return {
        "observations_n": cohort.observations_n,
        "providers_n": cohort.providers_n,
        "min_ars": float(cohort.min_ars),
        "median_ars": float(cohort.median_ars),
        "max_ars": float(cohort.max_ars),
        "spread_ratio": float(cohort.spread_ratio),
        "evidence_confidence": cohort.evidence_confidence,
        "range_ready": cohort.range_ready,
        "decision_ready": cohort.decision_ready,
    }


def _runtime_metrics(cohorts) -> dict[str, int]:
    return {
        "cohorts_total": len(cohorts),
        "cohorts_with_evidence": sum(item.observations_n > 0 for item in cohorts),
        "range_ready": sum(item.range_ready for item in cohorts),
        "decision_ready": sum(item.decision_ready for item in cohorts),
    }


def build_artifact(
    root: str | Path,
    output_path: str | Path,
    *,
    local_out_path: str | Path,
    remote_out_path: str | Path,
) -> dict[str, object]:
    root = Path(root).resolve()
    normalization_path = root / "data/semantic_normalization_v4.csv"
    evidence_path = root / "data/offer_evidence_v1.jsonl"
    with normalization_path.open(encoding="utf-8-sig", newline="") as handle:
        semantic_rows = list(csv.DictReader(handle))
    evidence = load_offer_evidence_sidecar(evidence_path)

    local_build, remote_build = build_runtime_pricing_statistics(
        normalization_path,
        evidence_path,
        repository_root=root,
        local_out_path=local_out_path,
        remote_out_path=remote_out_path,
    )
    before_local = cargar_cohortes_pricing(root / "data/local_pricing_stats_v2.csv")
    before_remote = cargar_cohortes_pricing(root / "data/remote_pricing_stats_v2.csv")
    after_local = cargar_cohortes_pricing(local_out_path, require_runtime_lineage_gate=True)
    after_remote = cargar_cohortes_pricing(remote_out_path, require_runtime_lineage_gate=True)
    before_cohorts = before_local + before_remote
    after_cohorts = after_local + after_remote
    before_by_id = {item.evidence_id: item for item in before_cohorts}
    after_by_id = {item.evidence_id: item for item in after_cohorts}

    decision_by_id = {
        item.observation_id: item
        for item in (*local_build.decisions, *remote_build.decisions)
    }
    members: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in semantic_rows:
        if row.get("observation_id") in decision_by_id:
            members[_cohort_id(row)].append(row)

    affected_cohorts = []
    for cohort_id, rows in sorted(members.items()):
        admitted_rows = [row for row in rows if decision_by_id[row["observation_id"]].admitted]
        excluded_rows = [row for row in rows if not decision_by_id[row["observation_id"]].admitted]
        if not excluded_rows:
            continue
        before = before_by_id.get(cohort_id)
        after = after_by_id.get(cohort_id)
        affected_cohorts.append(
            {
                "cohort_id": cohort_id,
                "observation_ids_before": [row["observation_id"] for row in rows],
                "observation_ids_admitted_after": [row["observation_id"] for row in admitted_rows],
                "observation_ids_excluded": [row["observation_id"] for row in excluded_rows],
                "exclusions": [
                    {
                        "observation_id": row["observation_id"],
                        "source_id": row["source"],
                        "price_ars": float(row["price_value"]),
                        "reason": decision_by_id[row["observation_id"]].exclusion_reason,
                        "detail": decision_by_id[row["observation_id"]].exclusion_detail,
                    }
                    for row in excluded_rows
                ],
                "before": _cohort_payload(before) if before else None,
                "after": _cohort_payload(after) if after else None,
            }
        )

    corpus = _jsonl(root / "data/language/real_query_corpus_v1.jsonl")
    readiness_before: Counter[str] = Counter()
    readiness_after: Counter[str] = Counter()
    failures_before: Counter[str] = Counter()
    failures_after: Counter[str] = Counter()
    outcomes_before: Counter[str] = Counter()
    outcomes_after: Counter[str] = Counter()
    affected_cases = []
    semantic_drift = []
    accepted_before = excluded_before = accepted_after = excluded_after = 0
    trace_parity_mismatches = []

    for record in corpus:
        query = str(record["query_raw"])
        before_result = resolver_consulta_pricing(
            query,
            local_cohortes=before_local,
            remote_cohortes=before_remote,
            language_evidence_type=str(record["provenance"]),
        )
        after_result = resolver_consulta_pricing(
            query,
            local_cohortes=after_local,
            remote_cohortes=after_remote,
            language_evidence_type=str(record["provenance"]),
        )
        before_trace = trace_real_world_query(
            query,
            local_cohortes=before_local,
            remote_cohortes=before_remote,
            source_case_id=f"lineage-before:{record['id']}",
            case_origin=str(record["provenance"]),
        )
        after_trace = trace_real_world_query(
            query,
            local_cohortes=after_local,
            remote_cohortes=after_remote,
            source_case_id=f"lineage-after:{record['id']}",
            case_origin=str(record["provenance"]),
        )
        readiness_before[before_result.status] += 1
        readiness_after[after_result.status] += 1
        failures_before.update(item.value for item in before_trace.failures)
        failures_after.update(item.value for item in after_trace.failures)
        before_outcome = classify(record, before_result)[0]
        after_outcome = classify(record, after_result)[0]
        accepted_before += len(before_trace.accepted_evidence)
        excluded_before += len(before_trace.excluded_evidence)
        accepted_after += len(after_trace.accepted_evidence)
        excluded_after += len(after_trace.excluded_evidence)

        before_semantic = _semantic_projection(before_trace)
        after_semantic = _semantic_projection(after_trace)
        if before_semantic != after_semantic:
            semantic_drift.append(str(record["id"]))
        if (
            after_outcome == "WRONG_INTERPRETATION"
            and before_outcome != "WRONG_INTERPRETATION"
            and before_semantic == after_semantic
            and before_result.status in {"RANGE_READY", "DECISION_READY"}
            and after_result.status in {"INSUFFICIENT_EVIDENCE", "NO_EVIDENCE"}
        ):
            after_outcome = "EXPECTED_SAFETY_CHANGE"
        outcomes_before[before_outcome] += 1
        outcomes_after[after_outcome] += 1

        expected_evidence = (
            ()
            if after_result.evidence is None or after_result.evidence.evidence_id is None
            else (after_result.evidence.evidence_id,)
        )
        if after_trace.accepted_evidence != expected_evidence:
            trace_parity_mismatches.append(str(record["id"]))

        response_changed = (
            before_result.status != after_result.status
            or before_trace.public_response != after_trace.public_response
        )
        if response_changed:
            affected_cases.append(
                {
                    "case_id": record["id"],
                    "readiness_before": before_result.status,
                    "readiness_after": after_result.status,
                    "response_before": before_trace.public_response,
                    "response_after": after_trace.public_response,
                    "classification": (
                        "UNEXPECTED_DRIFT"
                        if str(record["id"]) in semantic_drift
                        else "EXPECTED_SAFETY_CHANGE"
                    ),
                }
            )

    human_record = _jsonl(root / "data/field/human_real_cases_v1.jsonl")[0]
    human_query = str(human_record["raw_user_input"])
    human_before = trace_real_world_query(
        human_query,
        local_cohortes=before_local,
        remote_cohortes=before_remote,
        source_case_id="lineage-before:founder-20260823-001",
        case_origin="HUMAN_REAL",
    )
    human_after = trace_real_world_query(
        human_query,
        local_cohortes=after_local,
        remote_cohortes=after_remote,
        source_case_id="lineage-after:founder-20260823-001",
        case_origin="HUMAN_REAL",
    )

    before_metrics = _runtime_metrics(before_cohorts)
    after_metrics = _runtime_metrics(after_cohorts)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "start_head": START_HEAD,
        "debt_id": "TD-001",
        "observations_total": len(semantic_rows),
        "raw_reproducible_before": sum(
            item.lineage.linkage_status == "TRACEABLE_RAW" for item in evidence.values()
        ),
        "runtime_admitted_before": local_build.eligible_before + remote_build.eligible_before,
        "runtime_admitted_after": local_build.admitted + remote_build.admitted,
        "excluded_missing_lineage": local_build.excluded + remote_build.excluded,
        "runtime_cohorts_before": before_metrics,
        "runtime_cohorts_after": after_metrics,
        "affected_cohorts": affected_cohorts,
        "affected_cases": affected_cases,
        "range_ready_before": before_metrics["range_ready"],
        "range_ready_after": after_metrics["range_ready"],
        "decision_ready_before": before_metrics["decision_ready"],
        "decision_ready_after": after_metrics["decision_ready"],
        "provider_counts_before_after": [
            {
                "cohort_id": item["cohort_id"],
                "before": item["before"]["providers_n"] if item["before"] else 0,
                "after": item["after"]["providers_n"] if item["after"] else 0,
            }
            for item in affected_cohorts
        ],
        "trace_engine_parity": {
            "value": not trace_parity_mismatches,
            "mismatches": trace_parity_mismatches,
        },
        "human_real_001": {
            "case_id": human_record["case_id"],
            "readiness_before": human_before.readiness,
            "readiness_after": human_after.readiness,
            "intent": human_after.intent_result,
            "canonical_services": human_after.parser_result["canonical_services"],
            "device": human_after.economic_dimensions["device"]["value"],
            "location": human_after.economic_dimensions["location"]["value"],
            "currency": human_after.economic_dimensions["currency"]["value"],
            "price_scope": human_after.economic_dimensions["price_scope"]["value"],
            "semantic_drift": _semantic_projection(human_before) != _semantic_projection(human_after),
        },
        "corpus_50": {
            "cases": len(corpus),
            "parse_failures_before": failures_before["PARSE_FAILURE"],
            "parse_failures_after": failures_after["PARSE_FAILURE"],
            "intent_failures_before": failures_before["INTENT_FAILURE"],
            "intent_failures_after": failures_after["INTENT_FAILURE"],
            "wrong_interpretations_before": outcomes_before["WRONG_INTERPRETATION"],
            "wrong_interpretations_after": outcomes_after["WRONG_INTERPRETATION"],
            "expected_safety_changes_after": outcomes_after["EXPECTED_SAFETY_CHANGE"],
            "accepted_evidence_before": accepted_before,
            "accepted_evidence_after": accepted_after,
            "excluded_evidence_before": excluded_before,
            "excluded_evidence_after": excluded_after,
            "failure_taxonomy_before": dict(sorted(failures_before.items())),
            "failure_taxonomy_after": dict(sorted(failures_after.items())),
            "readiness_distribution_before": dict(sorted(readiness_before.items())),
            "readiness_distribution_after": dict(sorted(readiness_after.items())),
            "public_responses_changed": len(affected_cases),
        },
        "public_safety_changes": [
            item["case_id"]
            for item in affected_cases
            if item["classification"] == "EXPECTED_SAFETY_CHANGE"
        ],
        "unexpected_drift": [
            item["case_id"]
            for item in affected_cases
            if item["classification"] == "UNEXPECTED_DRIFT"
        ],
        "unexpected_semantic_drift": len(semantic_drift),
        "historical_rows_rewritten": False,
        "promotion_authorized": False,
        "runtime_learning_writes": 0,
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", required=True)
    parser.add_argument("--local-out", required=True)
    parser.add_argument("--remote-out", required=True)
    args = parser.parse_args()
    payload = build_artifact(
        args.root,
        args.out,
        local_out_path=args.local_out,
        remote_out_path=args.remote_out,
    )
    print(json.dumps({
        "artifact": args.out,
        "runtime_admitted_before": payload["runtime_admitted_before"],
        "runtime_admitted_after": payload["runtime_admitted_after"],
        "excluded_missing_lineage": payload["excluded_missing_lineage"],
        "trace_engine_parity": payload["trace_engine_parity"]["value"],
        "unexpected_semantic_drift": payload["unexpected_semantic_drift"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
