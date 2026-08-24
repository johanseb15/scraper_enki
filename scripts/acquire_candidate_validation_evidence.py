# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

from argparse import ArgumentParser
from pathlib import Path

from src.infraestructura.candidate_validation_evidence_acquisition import acquire_candidate_validation_evidence


CANDIDATE_ID = "knowledge-candidate:3190e09c277a38b6330d"


def main():
    parser = ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    root = Path(__file__).parents[1]
    metrics = acquire_candidate_validation_evidence(root, Path(args.out_dir), candidate_id=CANDIDATE_ID)
    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
