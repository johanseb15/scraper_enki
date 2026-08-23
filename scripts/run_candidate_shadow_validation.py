from pathlib import Path

from src.infraestructura.candidate_shadow_validation_runner import run_candidate_shadow_validation


CANDIDATE_ID = "knowledge-candidate:3190e09c277a38b6330d"


def main():
    root = Path(__file__).parents[1]
    metrics = run_candidate_shadow_validation(
        root, candidate_id=CANDIDATE_ID,
        audit_path=root / "data/candidate_shadow_validation_audit_v1.json",
        dataset_path=root / "data/candidate_shadow_validation_dataset_v1.jsonl",
        results_path=root / "data/candidate_shadow_validation_results_v1.jsonl",
        summary_path=root / "data/candidate_shadow_validation_summary_v1.json",
        requests_path=root / "data/candidate_shadow_validation_evidence_requests_v1.jsonl",
    )
    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
