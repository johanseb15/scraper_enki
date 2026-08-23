# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

from pathlib import Path

from src.infraestructura.price_scope_reconciliation_artifact import build_price_scope_reconciliation


def main():
    root = Path(__file__).parents[1]
    metrics = build_price_scope_reconciliation(root, root / "data")
    for key, value in metrics.items(): print(f"{key}={value}")


if __name__ == "__main__": main()
