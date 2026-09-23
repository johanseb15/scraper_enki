from __future__ import annotations

import re
import unicodedata

from src.dominio.hardware_signals import extract_hardware_signals
from src.dominio.semantic_observation import (
    HardwareMeaning,
    HardwareMeaningKind,
    SemanticObservation,
    SemanticObservationRole,
)


def interpret_hardware_meaning(observation: SemanticObservation) -> HardwareMeaning:
    if observation.semantic_role is not SemanticObservationRole.HARDWARE_PRODUCT:
        raise ValueError(
            "interpret_hardware_meaning requires a HARDWARE_PRODUCT observation."
        )

    raw = observation.raw_expression
    folded = _fold(raw)
    signals = extract_hardware_signals(raw)

    if _looks_like_service_action(folded):
        return HardwareMeaning(
            source_expression=raw,
            meaning_kind=HardwareMeaningKind.SERVICE_LIKE_CONFLICT,
            provenance=observation.interpretation_provenance,
            families=signals.families,
            brand_signals=signals.brand_signals,
            variant_signals=signals.variant_signals,
            spec_signals=signals.spec_signals,
        )

    families = signals.families
    if len(families) == 1:
        kind = HardwareMeaningKind.SINGLE_COMPONENT_FAMILY
    elif len(families) >= 2:
        kind = HardwareMeaningKind.MULTI_COMPONENT_SYSTEM
    else:
        kind = HardwareMeaningKind.UNKNOWN

    return HardwareMeaning(
        source_expression=raw,
        meaning_kind=kind,
        provenance=observation.interpretation_provenance,
        families=families,
        brand_signals=signals.brand_signals,
        variant_signals=signals.variant_signals,
        spec_signals=signals.spec_signals,
    )


def _looks_like_service_action(folded: str) -> bool:
    return bool(
        re.search(
            r"\b(?:cambio|cambiar|reemplazo|reemplazar|instalacion|instalar|"
            r"reparacion|reparar|upgrade|ampliacion)\b",
            folded,
        )
    )



def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())
