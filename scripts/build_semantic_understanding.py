from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import csv
from collections import Counter
from pathlib import Path

from src.infraestructura.semantic_understanding_artifact import (
    write_semantic_understanding_csv,
)
from src.infraestructura.semantic_understanding_batch import (
    compose_semantic_understanding_rows,
)


def build_semantic_understanding_artifact(
    input_csv: str | Path,
    output_csv: str | Path,
    *,
    interpretation_version: str | None = None,
) -> Path:
    input_path = Path(input_csv)
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    envelopes = compose_semantic_understanding_rows(
        rows,
        interpretation_reference=str(input_path),
        interpretation_version=interpretation_version,
    )

    if len(envelopes) != len(rows):
        raise ValueError(
            f"Cardinality mismatch: input={len(rows)} output={len(envelopes)}"
        )

    ids = [envelope.observation.observation_id for envelope in envelopes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate observation_id values in semantic understanding artifact.")

    output_path = write_semantic_understanding_csv(envelopes, output_csv)

    status_counts = Counter(envelope.status.value for envelope in envelopes)
    print(f"INPUT_ROWS={len(rows)}")
    print(f"OUTPUT_ROWS={len(envelopes)}")
    print(f"OUTPUT_PATH={output_path}")
    for status, count in sorted(status_counts.items()):
        print(f"STATUS_{status}={count}")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build read-only semantic-understanding sidecar CSV."
    )
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--version", default="semantic-understanding-artifact-v1")
    args = parser.parse_args()

    build_semantic_understanding_artifact(
        args.input_csv,
        args.output_csv,
        interpretation_version=args.version,
    )


if __name__ == "__main__":
    main()
