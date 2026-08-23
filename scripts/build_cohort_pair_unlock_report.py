from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json

from src.infraestructura.cohort_pair_unlock_report import build_cohort_pair_unlock_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cohort pair before/after and information-gain report.")
    for name in ("before_shadow", "after_shadow", "planner", "pairs", "outcomes", "report"):
        parser.add_argument(name)
    args = parser.parse_args()
    metrics = build_cohort_pair_unlock_report(
        args.before_shadow, args.after_shadow, args.planner, args.pairs, args.outcomes, args.report,
    )
    for key, value in metrics.items():
        print(f"{key}={json.dumps(value)}")


if __name__ == "__main__":
    main()
