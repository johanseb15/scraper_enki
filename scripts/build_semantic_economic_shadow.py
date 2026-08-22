from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.aplicacion.semantic_economic_evidence_bridge import (
    SemanticEconomicEvidenceBridge,
)
from src.dominio.economic_evidence import EconomicEvidenceDimensionsV2
from src.infraestructura.semantic_economic_evidence_adapter import (
    compose_economic_evidence_records,
)
from src.infraestructura.economic_dimensions_artifact import build_dimension_metrics
from src.infraestructura.economic_dimensions_loader import (
    load_versioned_economic_dimensions_sidecar,
)
from src.infraestructura.economic_dimensions_v2_artifact import (
    build_migration_metrics,
    build_v2_dimension_metrics,
)
from src.infraestructura.semantic_economic_shadow_artifact import (
    build_shadow_metrics,
    write_semantic_economic_shadow_jsonl,
    write_shadow_summary,
)
from src.infraestructura.semantic_understanding_batch import (
    compose_semantic_understanding_rows,
)


def build_semantic_economic_shadow(
    input_csv: str | Path,
    output_jsonl: str | Path,
    *,
    version: str = "semantic-economic-bridge-v1",
    dimensions_path: str | Path | None = None,
    previous_dimensions_path: str | Path | None = None,
) -> dict[str, Any]:
    input_path = Path(input_csv)
    output_path = Path(output_jsonl)
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    envelopes = compose_semantic_understanding_rows(
        rows,
        interpretation_reference=str(input_path),
        interpretation_version=version,
    )
    ids = [item.observation.observation_id for item in envelopes]
    if len(envelopes) != len(rows):
        raise ValueError(f"Cardinality mismatch: input={len(rows)} output={len(envelopes)}")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate observation_id values in shadow input.")

    dimensions = (
        load_versioned_economic_dimensions_sidecar(dimensions_path)
        if dimensions_path is not None else {}
    )
    if dimensions and set(dimensions) != set(ids):
        missing = sorted(set(ids) - set(dimensions))
        extra = sorted(set(dimensions) - set(ids))
        raise ValueError(
            f"Dimension sidecar observation_id mismatch: missing={missing} extra={extra}"
        )
    evidence = compose_economic_evidence_records(
        rows,
        envelopes,
        dimensions_by_observation_id=dimensions,
    )
    bridge = SemanticEconomicEvidenceBridge(evidence)
    contexts = tuple(bridge.resolve(envelope) for envelope in envelopes)
    if len(contexts) != len(envelopes):
        raise ValueError("Shadow bridge caused silent data loss.")

    write_semantic_economic_shadow_jsonl(contexts, output_path, version=version)
    metrics = build_shadow_metrics(contexts)
    metrics.update(bridge.candidate_generation_metrics)
    if dimensions:
        first_dimension = next(iter(dimensions.values()))
        if isinstance(first_dimension, EconomicEvidenceDimensionsV2):
            metrics.update(build_v2_dimension_metrics(dimensions.values(), rows))
            if previous_dimensions_path is not None:
                previous = load_versioned_economic_dimensions_sidecar(previous_dimensions_path)
                metrics.update(build_migration_metrics(previous, dimensions))
        else:
            metrics.update(build_dimension_metrics(dimensions.values()))
    summary_path = output_path.with_suffix(".summary.json")
    write_shadow_summary(metrics, summary_path, version=version)

    print(f"INPUT_ROWS={len(rows)}")
    print(f"OUTPUT_ROWS={len(contexts)}")
    print(f"OUTPUT_PATH={output_path}")
    print(f"SUMMARY_PATH={summary_path}")
    for key, value in metrics.items():
        print(f"{key}={json.dumps(value, ensure_ascii=False, sort_keys=True)}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a read-only semantic-economic shadow evaluation artifact."
    )
    parser.add_argument("input_csv")
    parser.add_argument("output_jsonl")
    parser.add_argument("--version", default="semantic-economic-bridge-v1")
    parser.add_argument("--dimensions")
    parser.add_argument("--previous-dimensions")
    args = parser.parse_args()
    build_semantic_economic_shadow(
        args.input_csv,
        args.output_jsonl,
        version=args.version,
        dimensions_path=args.dimensions,
        previous_dimensions_path=args.previous_dimensions,
    )


if __name__ == "__main__":
    main()
