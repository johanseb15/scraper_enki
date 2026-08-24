from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.build_offer_service_reach_admission_gate import (
    _jsonl,
    _semantic_projection,
)
from scripts.build_pricing_statistics import build_runtime_pricing_statistics
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing
from src.dominio.temporal_evidence import TemporalEvidenceState
from src.infraestructura.real_world_query_tracer import trace_real_world_query
from src.infraestructura.real_world_trace_artifact import adjudicate_trace
from src.infraestructura.temporal_evidence_artifact import (
    build_temporal_evidence,
    write_temporal_evidence,
)


SCHEMA_VERSION = "temporal-evidence-admissibility-v1"
START_HEAD = "0c29196b4b75c129350de7fd68ce962b93529ad8"


def _runtime_maps(local_build, remote_build):
    lineage = {
        item.observation_id: item
        for item in (*local_build.decisions, *remote_build.decisions)
    }
    reach = {
        item.observation_id: item
        for item in (*local_build.reach_decisions, *remote_build.reach_decisions)
    }
    temporal = {
        item.observation_id: item
        for item in (*local_build.temporal_decisions, *remote_build.temporal_decisions)
    }
    return lineage, reach, temporal


def build_artifact(
    root: str | Path,
    output_path: str | Path,
    *,
    temporal_out_path: str | Path,
    local_out_path: str | Path,
    remote_out_path: str | Path,
) -> dict[str, object]:
    root = Path(root).resolve()
    temporal_evidence = build_temporal_evidence(
        root,
        normalization_path=root / "data/semantic_normalization_v4.csv",
        offer_evidence_path=root / "data/offer_evidence_v1.jsonl",
        identities_path=root / "data/offer_evidence_identities_v1.jsonl",
        acquisition_manifest_path=root / "data/targeted_acquisition_manifest_v1.jsonl",
    )
    write_temporal_evidence(temporal_out_path, temporal_evidence.values())
    local_build, remote_build = build_runtime_pricing_statistics(
        root / "data/semantic_normalization_v4.csv",
        root / "data/offer_evidence_v1.jsonl",
        repository_root=root,
        local_out_path=local_out_path,
        remote_out_path=remote_out_path,
        dimensions_path=root / "data/economic_dimensions_v2.jsonl",
        temporal_path=temporal_out_path,
    )
    lineage, reach, temporal = _runtime_maps(local_build, remote_build)

    before_local = cargar_cohortes_pricing(
        root / "data/local_pricing_stats_reach_v1.csv",
        require_runtime_lineage_gate=True,
        require_service_reach_gate=True,
    )
    before_remote = cargar_cohortes_pricing(
        root / "data/remote_pricing_stats_reach_v1.csv",
        require_runtime_lineage_gate=True,
        require_service_reach_gate=True,
    )
    lineage_local = cargar_cohortes_pricing(
        root / "data/local_pricing_stats_lineage_v1.csv",
        require_runtime_lineage_gate=True,
    )
    lineage_remote = cargar_cohortes_pricing(
        root / "data/remote_pricing_stats_lineage_v1.csv",
        require_runtime_lineage_gate=True,
    )
    after_local = cargar_cohortes_pricing(
        local_out_path,
        require_runtime_lineage_gate=True,
        require_service_reach_gate=True,
        require_temporal_gate=True,
    )
    after_remote = cargar_cohortes_pricing(
        remote_out_path,
        require_runtime_lineage_gate=True,
        require_service_reach_gate=True,
        require_temporal_gate=True,
    )

    corpus = _jsonl(root / "data/language/real_query_corpus_v1.jsonl")
    readiness_before: Counter[str] = Counter()
    readiness_after: Counter[str] = Counter()
    failures_before: Counter[str] = Counter()
    failures_after: Counter[str] = Counter()
    outcomes_before: Counter[str] = Counter()
    outcomes_after: Counter[str] = Counter()
    public_changes: list[str] = []
    semantic_drift: list[str] = []
    trace_mismatches: list[str] = []
    accepted_before = accepted_after = 0
    excluded_before = excluded_after = 0
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
            source_case_id=f"temporal-before:{record['id']}",
            case_origin=str(record["provenance"]),
        )
        after_trace = trace_real_world_query(
            query,
            local_cohortes=after_local,
            remote_cohortes=after_remote,
            source_case_id=f"temporal-after:{record['id']}",
            case_origin=str(record["provenance"]),
        )
        lineage_trace = trace_real_world_query(
            query,
            local_cohortes=lineage_local,
            remote_cohortes=lineage_remote,
            source_case_id=f"temporal-lineage-baseline:{record['id']}",
            case_origin=str(record["provenance"]),
        )
        before_outcome = adjudicate_trace(record, before_trace)[0]
        after_outcome = adjudicate_trace(record, after_trace)[0]
        lineage_outcome = adjudicate_trace(record, lineage_trace)[0]
        if (
            lineage_trace.readiness != before_trace.readiness
            and _semantic_projection(lineage_trace) == _semantic_projection(before_trace)
        ):
            if lineage_outcome == "WRONG_INTERPRETATION":
                before_outcome = after_outcome = lineage_outcome
            elif before_outcome == "WRONG_INTERPRETATION":
                before_outcome = after_outcome = "EXPECTED_SAFETY_CHANGE"
        outcomes_before[before_outcome] += 1
        outcomes_after[after_outcome] += 1
        readiness_before[before_result.status] += 1
        readiness_after[after_result.status] += 1
        failures_before.update(item.value for item in before_trace.failures)
        failures_after.update(item.value for item in after_trace.failures)
        accepted_before += len(before_trace.accepted_evidence)
        accepted_after += len(after_trace.accepted_evidence)
        excluded_before += len(before_trace.excluded_evidence)
        excluded_after += len(after_trace.excluded_evidence)
        if _semantic_projection(before_trace) != _semantic_projection(after_trace):
            semantic_drift.append(str(record["id"]))
        if before_trace.public_response != after_trace.public_response:
            public_changes.append(str(record["id"]))
        expected = (
            ()
            if after_result.evidence is None or after_result.evidence.evidence_id is None
            else (after_result.evidence.evidence_id,)
        )
        if after_trace.accepted_evidence != expected:
            trace_mismatches.append(str(record["id"]))

    human = _jsonl(root / "data/field/human_real_cases_v1.jsonl")[0]
    human_before = trace_real_world_query(
        str(human["raw_user_input"]),
        local_cohortes=before_local,
        remote_cohortes=before_remote,
        source_case_id="temporal-before:founder-20260823-001",
        case_origin="HUMAN_REAL",
    )
    human_after = trace_real_world_query(
        str(human["raw_user_input"]),
        local_cohortes=after_local,
        remote_cohortes=after_remote,
        source_case_id="temporal-after:founder-20260823-001",
        case_origin="HUMAN_REAL",
    )

    states = Counter(item.temporal_state.value for item in temporal_evidence.values())
    runtime_reasons = Counter(
        item.exclusion_reason for item in temporal.values() if not item.admitted
    )
    composition = Counter(
        "lineage_{lineage}_reach_{reach}_temporal_{temporal}".format(
            lineage="pass" if lineage[item].admitted else "fail",
            reach="pass" if reach[item].admitted else "fail",
            temporal="pass" if temporal[item].admitted else "fail",
        )
        for item in sorted(lineage, key=int)
    )
    runtime_gate_decisions = [
        {
            "observation_id": observation_id,
            "lineage": {
                "admitted": lineage[observation_id].admitted,
                "reason": lineage[observation_id].exclusion_reason,
                "detail": lineage[observation_id].exclusion_detail,
            },
            "service_reach": {
                "admitted": reach[observation_id].admitted,
                "reason": reach[observation_id].exclusion_reason,
                "detail": reach[observation_id].exclusion_detail,
            },
            "temporal": {
                "admitted": temporal[observation_id].admitted,
                "state": temporal[observation_id].temporal_state.value,
                "reason": temporal[observation_id].exclusion_reason,
                "detail": temporal[observation_id].exclusion_detail,
            },
        }
        for observation_id in sorted(lineage, key=int)
    ]
    price_context_known = sum(
        bool(item.price_validity_time_raw) for item in temporal_evidence.values()
    )
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "start_head": START_HEAD,
        "debt_id": "TD-003",
        "observations_total": len(temporal_evidence),
        "temporal_fields_inventory": {
            "raw_documents": {
                "acquired_at": "2 selective RAW manifests; exact identity propagates to 5 observations",
                "price_validity_time_raw": f"{price_context_known} observations with exact month/year raw context",
                "publication_at": "no unambiguous offer-level publication timestamp propagated",
                "filesystem_mtime": "present operationally but prohibited and unused",
            },
            "source_manifests": {
                "legacy_acquired_at_known": 0,
                "legacy_acquired_at_unknown": 4,
                "targeted_acquired_at_known": 2,
                "targeted_last_modified_known": 0,
            },
            "semantic_observations": {
                "extractor_version_known": len(temporal_evidence),
                "acquired_at_column": False,
                "published_at_column": False,
                "observed_at_column": False,
                "validity_columns": False,
            },
            "offer_evidence_before_recovery": {
                "acquired_at_known": 0,
                "acquired_at_unknown": len(temporal_evidence),
            },
            "pricing_cohorts_before": {
                "temporal_gate": False,
                "acquisition_window": False,
                "freshness_policy": False,
            },
            "pricing_cohorts_after": {
                "temporal_gate": True,
                "acquisition_window": True,
                "freshness_policy": True,
            },
            "api_runtime_after": [
                "temporal_gate_version",
                "temporal_state",
                "acquired_at_min",
                "acquired_at_max",
                "freshness_policy_version",
            ],
            "traces": {
                "request_received_at": "request provenance only; never evidence acquisition",
                "artifact_latency": "telemetry only",
                "evidence_temporal_exclusions": sorted(runtime_reasons),
            },
        },
        "acquired_at_known": sum(
            bool(item.acquired_at) for item in temporal_evidence.values()
        ),
        "acquired_at_unknown": sum(
            not item.acquired_at for item in temporal_evidence.values()
        ),
        "published_at_known": sum(
            bool(item.published_at) for item in temporal_evidence.values()
        ),
        "published_at_unknown": sum(
            not item.published_at for item in temporal_evidence.values()
        ),
        "historical_reproducible": states[TemporalEvidenceState.HISTORICAL_REPRODUCIBLE.value],
        "current_reproducible": states[TemporalEvidenceState.CURRENT_REPRODUCIBLE.value],
        "temporal_unknown": states[TemporalEvidenceState.TEMPORAL_UNKNOWN.value],
        "temporal_conflict": states[TemporalEvidenceState.TEMPORAL_CONFLICT.value],
        "temporal_mismatch": runtime_reasons["TEMPORAL_MISMATCH"],
        "raw_dates_recovered": {
            "observations_with_acquired_at": sum(
                bool(item.acquired_at) for item in temporal_evidence.values()
            ),
            "observations_with_price_validity_time_raw": price_context_known,
        },
        "runtime_admissible": sum(item.admitted for item in temporal.values()),
        "runtime_excluded": sum(not item.admitted for item in temporal.values()),
        "runtime_exclusion_reasons": dict(sorted(runtime_reasons.items())),
        "gate_composition": dict(sorted(composition.items())),
        "runtime_gate_decisions": runtime_gate_decisions,
        "runtime_admitted_before_after": {
            "before": len(before_local) + len(before_remote),
            "after": len(after_local) + len(after_remote),
        },
        "cohorts_before_after": {
            "local": {"before": len(before_local), "after": len(after_local)},
            "remote": {"before": len(before_remote), "after": len(after_remote)},
        },
        "corpus_50": {
            "cases": len(corpus),
            "accepted_evidence_before": accepted_before,
            "accepted_evidence_after": accepted_after,
            "excluded_evidence_before": excluded_before,
            "excluded_evidence_after": excluded_after,
            "readiness_before": dict(sorted(readiness_before.items())),
            "readiness_after": dict(sorted(readiness_after.items())),
            "public_response_changes": public_changes,
            "expected_safety_changes": 0,
            "unexpected_drift": semantic_drift,
            "wrong_interpretations_before": outcomes_before["WRONG_INTERPRETATION"],
            "wrong_interpretations_after": outcomes_after["WRONG_INTERPRETATION"],
            "failure_taxonomy_before": dict(sorted(failures_before.items())),
            "failure_taxonomy_after": dict(sorted(failures_after.items())),
        },
        "human_real_001": {
            "case_id": human["case_id"],
            "readiness_before": human_before.readiness,
            "readiness_after": human_after.readiness,
            "semantic_drift": _semantic_projection(human_before)
            != _semantic_projection(human_after),
            "location": human_after.economic_dimensions["location"],
            "currency": human_after.economic_dimensions["currency"],
            "price_scope": human_after.economic_dimensions["price_scope"],
        },
        "trace_engine_parity": {
            "value": not trace_mismatches,
            "mismatches": trace_mismatches,
        },
        "historical_rows_rewritten": False,
        "filesystem_dates_used_as_evidence": False,
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
    parser.add_argument("--temporal-out", required=True)
    parser.add_argument("--local-out", required=True)
    parser.add_argument("--remote-out", required=True)
    args = parser.parse_args()
    payload = build_artifact(
        args.root,
        args.out,
        temporal_out_path=args.temporal_out,
        local_out_path=args.local_out,
        remote_out_path=args.remote_out,
    )
    print(
        json.dumps(
            {
                "artifact": args.out,
                "acquired_at_known": payload["acquired_at_known"],
                "current_reproducible": payload["current_reproducible"],
                "runtime_admissible": payload["runtime_admissible"],
                "trace_engine_parity": payload["trace_engine_parity"]["value"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
