# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

from argparse import ArgumentParser
from pathlib import Path

from src.infraestructura.candidate_shadow_validation_runner import run_candidate_shadow_validation


CANDIDATE_ID = "knowledge-candidate:3190e09c277a38b6330d"


def main():
    parser = ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).parents[1]
    output = args.out_dir
    metrics = run_candidate_shadow_validation(
        root, candidate_id=CANDIDATE_ID,
        audit_path=output / "candidate_shadow_validation_audit_v1.json",
        dataset_path=output / "candidate_shadow_validation_dataset_v1.jsonl",
        results_path=output / "candidate_shadow_validation_results_v1.jsonl",
        summary_path=output / "candidate_shadow_validation_summary_v1.json",
        requests_path=output / "candidate_shadow_validation_evidence_requests_v1.jsonl",
    )
    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
