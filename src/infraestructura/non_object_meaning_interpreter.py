from __future__ import annotations

import re
import unicodedata

from src.dominio.semantic_observation import (
    NonObjectMeaning,
    NonObjectMeaningKind,
    SemanticObservation,
    SemanticObservationRole,
)


def interpret_non_object_meaning(observation: SemanticObservation) -> NonObjectMeaning:
    if observation.semantic_role is not SemanticObservationRole.NON_OBJECT:
        raise ValueError(
            "interpret_non_object_meaning requires a NON_OBJECT observation."
        )

    raw = observation.raw_expression
    folded = _fold(raw)

    if re.fullmatch(r"precio\s*:?", folded):
        return _meaning(observation, NonObjectMeaningKind.PRICE_LABEL, ("PRICE_LABEL",))

    if re.fullmatch(r"desde", folded):
        return _meaning(
            observation,
            NonObjectMeaningKind.PRICING_LOWER_BOUND,
            ("LOWER_BOUND",),
        )

    if re.fullmatch(r"\$?\s*0(?:[.,]0+)?", folded):
        return _meaning(
            observation,
            NonObjectMeaningKind.ZERO_VALUE_PLACEHOLDER,
            ("ZERO_LITERAL", "DO_NOT_OVERRIDE_OBSERVED_PRICE"),
        )

    if re.fullmatch(r"disponible", folded):
        return _meaning(
            observation,
            NonObjectMeaningKind.AVAILABILITY_STATUS,
            ("AVAILABLE",),
        )

    if re.search(r"\bproblemas?\s+generales?\b", folded):
        return _meaning(
            observation,
            NonObjectMeaningKind.GENERIC_SERVICE_HEADING,
            ("GENERIC_SERVICE_CONTEXT",),
        )

    if (
        re.search(r"\bservice\b|\bservicio\b|\btecnico\b", folded)
        and re.search(r"\bprecio claro\b|\blo que hacemos\b", folded)
    ):
        return _meaning(
            observation,
            NonObjectMeaningKind.MARKETING_SERVICE_COPY,
            ("SERVICE_LANGUAGE", "MARKETING_LANGUAGE"),
        )

    return _meaning(observation, NonObjectMeaningKind.UNKNOWN, ())


def _meaning(
    observation: SemanticObservation,
    kind: NonObjectMeaningKind,
    signals: tuple[str, ...],
) -> NonObjectMeaning:
    return NonObjectMeaning(
        source_expression=observation.raw_expression,
        meaning_kind=kind,
        provenance=observation.interpretation_provenance,
        signals=signals,
    )


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())
