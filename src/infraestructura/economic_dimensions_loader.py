from __future__ import annotations

import json
from pathlib import Path

from src.infraestructura.economic_dimensions_artifact import (
    SIDECAR_SCHEMA_VERSION,
    load_economic_dimensions_sidecar,
)
from src.infraestructura.economic_dimensions_v2_artifact import (
    SIDECAR_V2_SCHEMA_VERSION,
    load_economic_dimensions_v2_sidecar,
)


def load_versioned_economic_dimensions_sidecar(path: str | Path):
    source = Path(path)
    first = next((line for line in source.read_text(encoding="utf-8").splitlines() if line.strip()), None)
    if first is None:
        return {}
    schema = json.loads(first).get("schema_version")
    if schema == SIDECAR_SCHEMA_VERSION:
        return load_economic_dimensions_sidecar(source)
    if schema == SIDECAR_V2_SCHEMA_VERSION:
        return load_economic_dimensions_v2_sidecar(source)
    raise ValueError(f"Unsupported economic dimension schema: {schema}")
