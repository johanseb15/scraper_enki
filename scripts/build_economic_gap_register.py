from __future__ import annotations

import argparse
import json

from src.infraestructura.economic_gap_artifact import build_gap_register


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic economic evidence gap register v1.")
    parser.add_argument("normalization_csv")
    parser.add_argument("registry_csv")
    parser.add_argument("dimensions_jsonl")
    parser.add_argument("output_jsonl")
    args = parser.parse_args()
    metrics = build_gap_register(
        args.normalization_csv,
        args.registry_csv,
        args.dimensions_jsonl,
        args.output_jsonl,
    )
    for key, value in metrics.items():
        print(f"{key}={json.dumps(value, ensure_ascii=False, sort_keys=True)}")


if __name__ == "__main__":
    main()
