from pathlib import Path

from src.infraestructura.price_scope_reconciliation_artifact import build_price_scope_reconciliation


def main():
    root = Path(__file__).parents[1]
    metrics = build_price_scope_reconciliation(root, root / "data")
    for key, value in metrics.items(): print(f"{key}={value}")


if __name__ == "__main__": main()
