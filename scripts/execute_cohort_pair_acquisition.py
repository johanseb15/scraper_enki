from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json

from src.infraestructura.cohort_pair_acquisition import execute_positive_pair_actions


def main() -> None:
    parser = argparse.ArgumentParser(description="Enforce positive counterfactual value before pair acquisition.")
    parser.add_argument("plan")
    parser.add_argument("outcomes")
    args = parser.parse_args()
    metrics = execute_positive_pair_actions(args.plan, args.outcomes)
    for key, value in metrics.items():
        print(f"{key}={json.dumps(value)}")


if __name__ == "__main__":
    main()
