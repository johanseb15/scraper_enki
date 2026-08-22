from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.dominio.semantic_understanding import SemanticUnderstandingEnvelope


FIELDNAMES = (
    "observation_id",
    "semantic_role",
    "understanding_status",
    "meaning_type",
    "meaning_json",
    "observation_provenance_json",
    "interpretation_provenance_json",
)


def write_semantic_understanding_csv(
    envelopes: tuple[SemanticUnderstandingEnvelope, ...],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for envelope in envelopes:
            writer.writerow(_row(envelope))

    return path


def _row(envelope: SemanticUnderstandingEnvelope) -> dict[str, str]:
    meaning = envelope.meaning
    return {
        "observation_id": envelope.observation.observation_id,
        "semantic_role": envelope.observation.semantic_role.value,
        "understanding_status": envelope.status.value,
        "meaning_type": type(meaning).__name__ if meaning is not None else "",
        "meaning_json": _json(meaning) if meaning is not None else "",
        "observation_provenance_json": _json(envelope.observation_provenance),
        "interpretation_provenance_json": _json(envelope.interpretation_provenance),
    }


def _json(value: Any) -> str:
    return json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(val) for key, val in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _jsonable(val) for key, val in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value
