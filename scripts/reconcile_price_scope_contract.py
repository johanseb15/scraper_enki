# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

from argparse import ArgumentParser
from pathlib import Path

from src.infraestructura.price_scope_reconciliation_artifact import build_price_scope_reconciliation


def main():
    parser = ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    root = Path(__file__).parents[1]
    metrics = build_price_scope_reconciliation(root, Path(args.out_dir))
    for key, value in metrics.items(): print(f"{key}={value}")


if __name__ == "__main__": main()
