from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
from pathlib import Path

from src.infraestructura.offer_observation_projection_artifact import (
    build_offer_observation_projection_bundle,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic OfferObservation projection artifacts "
            "into an explicit destination."
        )
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help=(
            "Explicit destination; no tracked historical path is "
            "overwritten by default."
        ),
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]

    metrics = build_offer_observation_projection_bundle(
        root=root,
        output_dir=Path(args.out_dir),
    )

    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
