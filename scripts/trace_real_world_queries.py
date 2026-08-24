# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

from argparse import ArgumentParser
from pathlib import Path

from src.infraestructura.real_world_trace_artifact import build_real_world_trace_artifacts


def main():
    parser = ArgumentParser(description="Build real-world trace artifacts into an explicit destination.")
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Explicit destination; no tracked historical path is overwritten by default.",
    )
    args = parser.parse_args()
    root = Path(__file__).parents[1]
    metrics = build_real_world_trace_artifacts(root, Path(args.out_dir))
    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
