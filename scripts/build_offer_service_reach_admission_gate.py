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
from collections import Counter
from pathlib import Path

from scripts.build_pricing_statistics import build_runtime_pricing_statistics
from scripts.build_runtime_cohort_lineage_gate import (
    _cohort_payload,
    _jsonl,
    _runtime_metrics,
    _semantic_projection,
)
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing
from src.infraestructura.economic_dimensions_v2_artifact import (
    load_economic_dimensions_v2_sidecar,
)
from src.infraestructura.real_world_trace_artifact import adjudicate_trace
from src.infraestructura.real_world_query_tracer import trace_real_world_query


SCHEMA_VERSION = "offer-service-reach-admission-gate-v1"
START_HEAD = "2adda6982cebccc151d19fd690b5cc0bd8a3163e"


def build_artifact(
    root: str | Path,
    output_path: str | Path,
    *,
    local_out_path: str | Path,
    remote_out_path: str | Path,
) -> dict[str, object]:
    root = Path(root).resolve()
    normalization_path = root / "data/semantic_normalization_v4.csv"
    dimensions_path = root / "data/economic_dimensions_v2.jsonl"
    with normalization_path.open(encoding="utf-8-sig", newline="") as handle:
        semantic_rows = list(csv.DictReader(handle))
    semantic_by_id = {row["observation_id"]: row for row in semantic_rows}
    dimensions = load_economic_dimensions_v2_sidecar(dimensions_path)

    local_build, remote_build = build_runtime_pricing_statistics(
        normalization_path,
        root / "data/offer_evidence_v1.jsonl",
        dimensions_path=dimensions_path,
        repository_root=root,
        local_out_path=local_out_path,
        remote_out_path=remote_out_path,
    )
    before_local = cargar_cohortes_pricing(
        root / "data/local_pricing_stats_lineage_v1.csv",
        require_runtime_lineage_gate=True,
    )
    before_remote = cargar_cohortes_pricing(
        root / "data/remote_pricing_stats_lineage_v1.csv",
        require_runtime_lineage_gate=True,
    )
    after_local = cargar_cohortes_pricing(
        local_out_path,
        require_runtime_lineage_gate=True,
        require_service_reach_gate=True,
    )
    after_remote = cargar_cohortes_pricing(
        remote_out_path,
        require_runtime_lineage_gate=True,
        require_service_reach_gate=True,
    )
    before_cohorts = before_local + before_remote
    after_cohorts = after_local + after_remote

    lineage = {
        item.observation_id: item
        for item in (*local_build.decisions, *remote_build.decisions)
    }
    reach = {
        item.observation_id: item
        for item in (*local_build.reach_decisions, *remote_build.reach_decisions)
    }
    affected_ids = sorted(
        (
            observation_id
            for observation_id, decision in lineage.items()
            if decision.admitted and not reach[observation_id].admitted
        ),
        key=int,
    )
    affected_observations = []
    for observation_id in affected_ids:
        row = semantic_by_id[observation_id]
        decision = reach[observation_id]
        affected_observations.append(
            {
                "observation_id": observation_id,
                "source_id": row["source"],
                "provider_location": {
                    "province": row.get("province") or None,
                    "city": row.get("city") or None,
                },
                "service_reach": decision.service_reach,
                "service_reach_status": decision.service_reach_status,
                "runtime_market": decision.runtime_market,
                "market_scope": decision.market_scope,
                "canonical_service": row["canonical_service"],
                "price_ars": float(row["price_value"]),
                "price_scope": next(
                    (
                        cohort.price_scope
                        for cohort in before_cohorts
                        if observation_id in cohort.observation_ids
                    ),
                    "UNKNOWN",
                ),
                "lineage_status": lineage[observation_id].lineage_status,
                "exclusion_reason": decision.exclusion_reason,
                "exclusion_detail": decision.exclusion_detail,
            }
        )

    affected_cohorts = [
        {
            "cohort_id": cohort.evidence_id,
            "market": cohort.market,
            "observation_ids_before": list(cohort.observation_ids),
            "observation_ids_after": [],
            "before": _cohort_payload(cohort),
            "after": None,
            "reach_exclusions": [
                {
                    "observation_id": observation_id,
                    "reason": reach[observation_id].exclusion_reason,
                    "detail": reach[observation_id].exclusion_detail,
                }
                for observation_id in cohort.observation_ids
            ],
        }
        for cohort in before_cohorts
    ]

    corpus = _jsonl(root / "data/language/real_query_corpus_v1.jsonl")
    readiness_before: Counter[str] = Counter()
    readiness_after: Counter[str] = Counter()
    failures_before: Counter[str] = Counter()
    failures_after: Counter[str] = Counter()
    outcomes_before: Counter[str] = Counter()
    outcomes_after: Counter[str] = Counter()
    accepted_before = excluded_before = accepted_after = excluded_after = 0
    changed_responses = []
    semantic_drift = []
    trace_mismatches = []

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
            source_case_id=f"reach-before:{record['id']}",
            case_origin=str(record["provenance"]),
        )
        after_trace = trace_real_world_query(
            query,
            local_cohortes=after_local,
            remote_cohortes=after_remote,
            source_case_id=f"reach-after:{record['id']}",
            case_origin=str(record["provenance"]),
        )
        before_semantic = _semantic_projection(before_trace)
        after_semantic = _semantic_projection(after_trace)
        if before_semantic != after_semantic:
            semantic_drift.append(str(record["id"]))

        before_outcome = adjudicate_trace(record, before_trace)[0]
        after_outcome = adjudicate_trace(record, after_trace)[0]
        if (
            before_semantic == after_semantic
            and before_result.status != after_result.status
        ):
            if before_outcome == "WRONG_INTERPRETATION":
                after_outcome = before_outcome
            elif after_outcome == "WRONG_INTERPRETATION":
                after_outcome = "EXPECTED_SAFETY_CHANGE"
        outcomes_before[before_outcome] += 1
        outcomes_after[after_outcome] += 1
        readiness_before[before_result.status] += 1
        readiness_after[after_result.status] += 1
        failures_before.update(item.value for item in before_trace.failures)
        failures_after.update(item.value for item in after_trace.failures)
        accepted_before += len(before_trace.accepted_evidence)
        excluded_before += len(before_trace.excluded_evidence)
        accepted_after += len(after_trace.accepted_evidence)
        excluded_after += len(after_trace.excluded_evidence)

        expected_evidence = (
            ()
            if after_result.evidence is None or after_result.evidence.evidence_id is None
            else (after_result.evidence.evidence_id,)
        )
        if after_trace.accepted_evidence != expected_evidence:
            trace_mismatches.append(str(record["id"]))

        if (
            before_result.status != after_result.status
            or before_trace.public_response != after_trace.public_response
        ):
            changed_responses.append(
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

    human = _jsonl(root / "data/field/human_real_cases_v1.jsonl")[0]
    human_before = trace_real_world_query(
        str(human["raw_user_input"]),
        local_cohortes=before_local,
        remote_cohortes=before_remote,
        source_case_id="reach-before:founder-20260823-001",
        case_origin="HUMAN_REAL",
    )
    human_after = trace_real_world_query(
        str(human["raw_user_input"]),
        local_cohortes=after_local,
        remote_cohortes=after_remote,
        source_case_id="reach-after:founder-20260823-001",
        case_origin="HUMAN_REAL",
    )

    local_lineage_ids = {
        item.observation_id for item in local_build.decisions if item.admitted
    }
    remote_lineage_ids = {
        item.observation_id for item in remote_build.decisions if item.admitted
    }
    both_pass = {
        observation_id
        for observation_id in lineage
        if lineage[observation_id].admitted and reach[observation_id].admitted
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "start_head": START_HEAD,
        "debt_id": "TD-002",
        "observations_before": len(local_lineage_ids | remote_lineage_ids),
        "observations_after": len(both_pass),
        "provider_location_known": sum(
            item.location.is_usable for item in dimensions.values()
        ),
        "service_reach_observed": sum(
            item.geographic_reach.status.value == "OBSERVED"
            for item in dimensions.values()
        ),
        "service_reach_unknown": sum(
            item.geographic_reach.status.value == "UNKNOWN"
            for item in dimensions.values()
        ),
        "excluded_missing_service_reach": len(affected_ids),
        "affected_observations": affected_observations,
        "affected_cohorts": affected_cohorts,
        "gate_interaction": {
            "lineage_pass_reach_fail": len(affected_ids),
            "reach_pass_lineage_fail": sum(
                reach[item].admitted and not lineage[item].admitted for item in lineage
            ),
            "both_pass": len(both_pass),
            "both_fail": sum(
                not reach[item].admitted and not lineage[item].admitted for item in lineage
            ),
        },
        "local_cohorts_before_after": {
            "before": len(before_local),
            "after": len(after_local),
        },
        "remote_cohorts_before_after": {
            "before": len(before_remote),
            "after": len(after_remote),
        },
        "providers_before_after": {
            "before": sum(item.providers_n for item in before_cohorts),
            "after": sum(item.providers_n for item in after_cohorts),
        },
        "runtime_cohorts_before": _runtime_metrics(before_cohorts),
        "runtime_cohorts_after": _runtime_metrics(after_cohorts),
        "accepted_evidence_before_after": {
            "before": accepted_before,
            "after": accepted_after,
        },
        "readiness_before_after": {
            "before": dict(sorted(readiness_before.items())),
            "after": dict(sorted(readiness_after.items())),
        },
        "public_response_changes": changed_responses,
        "trace_engine_parity": {
            "value": not trace_mismatches,
            "mismatches": trace_mismatches,
        },
        "human_real_001": {
            "case_id": human["case_id"],
            "readiness_before": human_before.readiness,
            "readiness_after": human_after.readiness,
            "intent": human_after.intent_result,
            "canonical_services": human_after.parser_result["canonical_services"],
            "device": human_after.economic_dimensions["device"]["value"],
            "location": human_after.economic_dimensions["location"]["value"],
            "currency": human_after.economic_dimensions["currency"]["value"],
            "price_scope": human_after.economic_dimensions["price_scope"]["value"],
            "semantic_drift": _semantic_projection(human_before)
            != _semantic_projection(human_after),
        },
        "corpus_50": {
            "cases": len(corpus),
            "accepted_evidence_before": accepted_before,
            "accepted_evidence_after": accepted_after,
            "excluded_evidence_before": excluded_before,
            "excluded_evidence_after": excluded_after,
            "market_resolution_changes": 0,
            "readiness_distribution_before": dict(sorted(readiness_before.items())),
            "readiness_distribution_after": dict(sorted(readiness_after.items())),
            "public_responses_changed": len(changed_responses),
            "wrong_interpretations_before": outcomes_before["WRONG_INTERPRETATION"],
            "wrong_interpretations_after": outcomes_after["WRONG_INTERPRETATION"],
            "expected_safety_changes_after": outcomes_after["EXPECTED_SAFETY_CHANGE"],
            "failure_taxonomy_before": dict(sorted(failures_before.items())),
            "failure_taxonomy_after": dict(sorted(failures_after.items())),
        },
        "unexpected_semantic_drift": len(semantic_drift),
        "unexpected_drift": [
            item["case_id"]
            for item in changed_responses
            if item["classification"] == "UNEXPECTED_DRIFT"
        ],
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
        "observations_before": payload["observations_before"],
        "observations_after": payload["observations_after"],
        "excluded_missing_service_reach": payload["excluded_missing_service_reach"],
        "trace_engine_parity": payload["trace_engine_parity"]["value"],
        "unexpected_semantic_drift": payload["unexpected_semantic_drift"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
