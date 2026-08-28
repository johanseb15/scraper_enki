# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json
from pathlib import Path

from src.api.decision_pricing_contract import (
    DecisionPricingResponse,
)


def build_schema() -> dict:
    return DecisionPricingResponse.model_json_schema()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        required=True,
    )
    args = parser.parse_args()

    output = Path(args.out)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            build_schema(),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
