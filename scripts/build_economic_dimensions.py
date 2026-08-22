from __future__ import annotations

import argparse
import json

from src.infraestructura.economic_dimensions_artifact import (
    build_economic_dimensions_sidecar,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build reversible economic evidence dimensions sidecar."
    )
    parser.add_argument("normalization_csv")
    parser.add_argument("registry_csv")
    parser.add_argument("output_jsonl")
    parser.add_argument("--version", default="economic-evidence-dimensions-v1")
    args = parser.parse_args()
    metrics = build_economic_dimensions_sidecar(
        args.normalization_csv,
        args.registry_csv,
        args.output_jsonl,
        version=args.version,
    )
    for key, value in metrics.items():
        print(f"{key}={json.dumps(value, ensure_ascii=False, sort_keys=True)}")


if __name__ == "__main__":
    main()
