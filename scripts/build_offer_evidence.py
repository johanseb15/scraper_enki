from __future__ import annotations

import argparse
import json

from src.infraestructura.offer_evidence_artifact import build_offer_evidence_sidecar


def main() -> None:
    parser = argparse.ArgumentParser(description="Build raw-first offer reach and charged-scope evidence v1.")
    parser.add_argument("normalization_csv")
    parser.add_argument("registry_csv")
    parser.add_argument("raw_manifest_csv")
    parser.add_argument("output_jsonl")
    parser.add_argument("--version", default="offer-reach-charged-scope-evidence-v1")
    args = parser.parse_args()
    metrics = build_offer_evidence_sidecar(
        args.normalization_csv,
        args.registry_csv,
        args.raw_manifest_csv,
        args.output_jsonl,
        version=args.version,
    )
    for key, value in metrics.items():
        print(f"{key}={json.dumps(value, ensure_ascii=False, sort_keys=True)}")


if __name__ == "__main__":
    main()
