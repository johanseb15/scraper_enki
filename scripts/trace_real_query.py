# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing_runtime
from src.infraestructura.human_real_intake import ingest_human_real_case


def main():
    parser = ArgumentParser(description="Append one human real query trace through Enki's real runtime.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--case-id", required=True, help="Non-secret stable field-case identifier.")
    parser.add_argument("--founder-note")
    parser.add_argument("--expected-intent")
    parser.add_argument("--observed-problem")
    parser.add_argument("--out", default="data/field/human_real_query_traces_v1.jsonl")
    parser.add_argument("--cases-out", default="data/field/human_real_cases_v1.jsonl")
    args = parser.parse_args()
    local, remote = cargar_cohortes_pricing_runtime()
    trace, _ = ingest_human_real_case(
        case_path=Path(args.cases_out), trace_path=Path(args.out), raw_user_input=args.query,
        case_id=args.case_id, received_at=datetime.now(timezone.utc).isoformat(),
        local_cohortes=local, remote_cohortes=remote, founder_note=args.founder_note,
        expected_intent=args.expected_intent, observed_problem=args.observed_problem,
    )
    print(f"TRACE_ID={trace.trace_id}")
    print(f"READINESS={trace.readiness}")
    print(f"FAILURES={','.join(item.value for item in trace.failures)}")
    print(f"PROMOTION_AUTHORIZED={trace.promotion_authorized}")


if __name__ == "__main__":
    main()
