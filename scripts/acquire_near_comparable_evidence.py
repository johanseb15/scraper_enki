from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json

from src.infraestructura.targeted_evidence_acquisition import acquire_planned_sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Selectively reacquire deduplicated near-comparable sources.")
    parser.add_argument("plan")
    parser.add_argument("historical_manifest")
    parser.add_argument("raw_root")
    parser.add_argument("acquisition_manifest")
    args = parser.parse_args()
    metrics = acquire_planned_sources(args.plan, args.historical_manifest, args.raw_root, args.acquisition_manifest)
    for key, value in metrics.items():
        print(f"{key}={json.dumps(value, ensure_ascii=False, sort_keys=True)}")


if __name__ == "__main__":
    main()
