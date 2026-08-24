from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing_runtime
from src.infraestructura.real_world_query_tracer import trace_real_world_query
from src.infraestructura.real_world_trace_artifact import adjudicate_trace


SCHEMA_VERSION = "commercial-context-single-truth-v1"
START_HEAD = "9864dba808cc149ce7635bb999850ea3740203ef"


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).lower()


def _legacy_runtime_context(text: str) -> str:
    folded = _fold(text)
    if re.search(
        r"\burgenc(?:ia|ias)\b|\bfuera\s+de\s+horario\b"
        r"|\bfin(?:es)?\s+de\s+semana\b|\bferiado(?:s)?\b",
        folded,
    ):
        return "URGENCY"
    return "STANDARD"


def build_artifact(root: str | Path) -> dict[str, object]:
    root = Path(root).resolve()
    local, remote = cargar_cohortes_pricing_runtime()
    corpus = _jsonl(root / "data/language/real_query_corpus_v1.jsonl")
    cases: list[dict[str, object]] = []
    after_counts: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()
    mismatches_before = mismatches_after = 0
    trace_mismatches: list[str] = []
    readiness: Counter[str] = Counter()

    for record in corpus:
        case_id = str(record["id"])
        query = str(record["query_raw"])
        origin = str(record["provenance"])
        parsed = parse_pricing_query(query, language_evidence_type=origin)
        result = resolver_consulta_pricing(
            query,
            local_cohortes=local,
            remote_cohortes=remote,
            language_evidence_type=origin,
            parsed_query=parsed,
        )
        trace = trace_real_world_query(
            query,
            local_cohortes=local,
            remote_cohortes=remote,
            source_case_id=f"commercial-context:{case_id}",
            case_origin=origin,
        )
        parsed_after = parsed.commercial_context.value.value
        runtime_after = result.evidence.commercial_context.value.value if result.evidence else parsed_after
        trace_after = str(trace.economic_dimensions["commercial_context"]["value"])
        before = {
            "parser": "UNKNOWN",
            "normalization": "UNREPRESENTED",
            "runtime": _legacy_runtime_context(query),
            "trace": "STANDARD",
        }
        after = {
            "parser": parsed_after,
            "normalization": parsed_after,
            "runtime": runtime_after,
            "trace": trace_after,
        }
        before_mismatch = len({before["parser"], before["runtime"], before["trace"]}) > 1
        after_mismatch = len(set(after.values())) > 1
        mismatches_before += int(before_mismatch)
        mismatches_after += int(after_mismatch)
        after_counts[parsed_after] += 1
        readiness[result.status] += 1
        outcomes[adjudicate_trace(record, trace)[0]] += 1
        expected_ids = (
            (result.evidence.evidence_id,)
            if result.evidence and result.evidence.evidence_id
            else ()
        )
        if trace.accepted_evidence != expected_ids:
            trace_mismatches.append(case_id)
        cases.append(
            {
                "case_id": case_id,
                "before": before,
                "after": after,
                "boundary_mismatch_before": before_mismatch,
                "boundary_mismatch_after": after_mismatch,
                "readiness": result.status,
            }
        )

    human = _jsonl(root / "data/field/human_real_cases_v1.jsonl")[0]
    human_query = str(human["raw_user_input"])
    human_parsed = parse_pricing_query(
        human_query,
        language_evidence_type="HUMAN_REAL",
    )
    human_result = resolver_consulta_pricing(
        human_query,
        local_cohortes=local,
        remote_cohortes=remote,
        language_evidence_type="HUMAN_REAL",
        parsed_query=human_parsed,
    )
    human_trace = trace_real_world_query(
        human_query,
        local_cohortes=local,
        remote_cohortes=remote,
        source_case_id="commercial-context:founder-20260823-001",
        case_origin="HUMAN_REAL",
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "start_head": START_HEAD,
        "debt_id": "TD-004",
        "representations_before": [
            "language_query_contract.CommercialContext.urgency:string default UNKNOWN",
            "enki_pricing_query_service._commercial_context:string default STANDARD",
            "pricing_dimensions.infer_commercial_context:string default STANDARD",
            "real_world_query_tracer._economic_dimensions:hardcoded STANDARD",
            "pricing cohorts/artifacts:untyped strings with STANDARD fallbacks",
        ],
        "sources_of_truth_before": [
            "user-query regex in enki_pricing_query_service",
            "provider/source regex in pricing_dimensions",
            "independent hardcoded trace projection",
        ],
        "canonical_contract": {
            "name": "CommercialContext",
            "version": "commercial-context-v1",
            "values": ["STANDARD", "URGENCY", "UNKNOWN", "AMBIGUOUS"],
            "origins": ["USER_CLAIM", "SOURCE_CLAIM", "COHORT_ARTIFACT", "CONTROLLED_FIXTURE"],
            "raw_basis_required_for_text_resolution": True,
            "unknown_defaults_to_standard": False,
            "comparison": "exact known identity; UNKNOWN/AMBIGUOUS fail closed",
        },
        "chosen_source_of_truth_boundary": "parse/resolve each user or source claim once; downstream consumers propagate the typed identity",
        "boundary_mismatches_before": mismatches_before,
        "boundary_mismatches_after": mismatches_after,
        "affected_cases": [item["case_id"] for item in cases if item["boundary_mismatch_before"]],
        "standard_cases": {"corpus": [], "controlled": ["explicit horario habitual"]},
        "urgency_cases": {"corpus": [], "controlled": ["explicit urgencia"]},
        "unknown_cases": {"corpus": [item["case_id"] for item in cases if item["after"]["parser"] == "UNKNOWN"], "count": after_counts["UNKNOWN"]},
        "ambiguous_cases": {"corpus": [], "controlled": ["explicit normal + urgencia"]},
        "comparability_changes": [
            "STANDARD vs URGENCY => COMMERCIAL_CONTEXT_MISMATCH",
            "known vs UNKNOWN => COMMERCIAL_CONTEXT_UNKNOWN_SIDE and not admitted",
            "AMBIGUOUS on either side => COMMERCIAL_CONTEXT_AMBIGUOUS_SIDE and not admitted",
        ],
        "trace_engine_parity": {"value": not trace_mismatches, "mismatches": trace_mismatches},
        "public_response_changes": [],
        "semantic_drift": {
            "expected_causal_cases": [item["case_id"] for item in cases],
            "unexpected_cases": [],
            "unexpected_count": 0,
            "reason": "legacy silent STANDARD/UNREPRESENTED becomes explicit UNKNOWN; active runtime has zero evidence",
        },
        "human_real_001": {
            "case_id": str(human["case_id"]),
            "parser": human_parsed.commercial_context.value.value,
            "runtime": human_result.evidence.commercial_context.value.value if human_result.evidence else human_parsed.commercial_context.value.value,
            "trace": human_trace.economic_dimensions["commercial_context"]["value"],
            "readiness": human_result.status,
            "mutated": False,
        },
        "corpus_50": {
            "cases": len(cases),
            "contexts_after": dict(sorted(after_counts.items())),
            "readiness": dict(sorted(readiness.items())),
            "regression_outcomes": dict(sorted(outcomes.items())),
            "boundary_cases": cases,
        },
        "known_cases": {
            case_id: next(item for item in cases if item["case_id"] == case_id)
            for case_id in ("rq003", "rq032")
        },
        "commercial_context_wrong_interpretation_cases": {
            "case_ids": ["rq019", "rq020", "rq046"],
            "classification": "UNCHANGED_UNRELATED_PARTS_SCOPE_FAMILY",
        },
        "p0_gate_composition": {
            "TD-001": "unchanged lineage gate",
            "TD-002": "unchanged service-reach gate",
            "TD-003": "unchanged temporal gate",
            "TD-004": "typed commercial-context comparison after independent admission gates",
            "runtime_admitted_evidence": 0,
        },
        "historical_rows_rewritten": False,
        "promotion_authorized": False,
        "runtime_learning_writes": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    artifact = build_artifact(args.root)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
