from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
from pathlib import Path

from src.infraestructura.knowledge_candidate_artifact import build_knowledge_candidate_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Build read-only learning candidate artifacts.")
    parser.add_argument("--root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    output = args.out_dir
    metrics = build_knowledge_candidate_artifacts(
        root,
        audit=output / "knowledge_observation_audit_v1.json",
        candidates=output / "knowledge_candidates_v1.jsonl",
        summary=output / "knowledge_candidates_v1.summary.json",
        requests=output / "candidate_evidence_requests_v1.jsonl",
        plans=output / "candidate_shadow_validation_plans_v1.jsonl",
        alignment=output / "learning_rector_alignment_v1.json",
    )
    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
