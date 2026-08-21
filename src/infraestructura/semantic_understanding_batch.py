from __future__ import annotations

from collections.abc import Iterable, Mapping

from src.dominio.semantic_understanding import SemanticUnderstandingEnvelope
from src.infraestructura.semantic_observation_adapter import (
    semantic_observation_from_normalized_row,
)
from src.infraestructura.semantic_understanding_composer import (
    compose_semantic_understanding,
)


def compose_semantic_understanding_rows(
    rows: Iterable[Mapping[str, str]],
    *,
    interpretation_reference: str | None = None,
    interpretation_version: str | None = None,
) -> tuple[SemanticUnderstandingEnvelope, ...]:
    envelopes: list[SemanticUnderstandingEnvelope] = []

    for row in rows:
        observation = semantic_observation_from_normalized_row(
            row,
            interpretation_reference=interpretation_reference,
            interpretation_version=interpretation_version,
        )
        envelopes.append(compose_semantic_understanding(observation))

    return tuple(envelopes)
