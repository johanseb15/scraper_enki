from __future__ import annotations

import re
import unicodedata

from src.dominio.semantic_observation import (
    LogisticsMeaning,
    LogisticsMeaningKind,
    SemanticObservation,
    SemanticObservationRole,
)


def interpret_logistics_meaning(observation: SemanticObservation) -> LogisticsMeaning:
    if observation.semantic_role is not SemanticObservationRole.LOGISTICS_CONTEXT:
        raise ValueError(
            "interpret_logistics_meaning requires a LOGISTICS_CONTEXT observation."
        )

    raw = observation.raw_expression
    folded = _fold(raw)
    channels = _channels(folded)
    destinations = _destinations(folded)
    carriers = _carriers(folded)
    coverage = _coverage_signals(folded)

    if "MOTORBIKE_COURIER" in channels and coverage:
        kind = LogisticsMeaningKind.LOCAL_COURIER_DELIVERY
    elif "HOME" in destinations:
        kind = LogisticsMeaningKind.HOME_DELIVERY
    elif "BRANCH" in destinations and "DELIVERY" in channels:
        kind = LogisticsMeaningKind.BRANCH_DELIVERY
    elif "BRANCH" in destinations or "PICKUP_POINT" in destinations:
        kind = LogisticsMeaningKind.PICKUP_POINT
    else:
        kind = LogisticsMeaningKind.UNKNOWN

    return LogisticsMeaning(
        source_expression=raw,
        meaning_kind=kind,
        provenance=observation.interpretation_provenance,
        channels=channels,
        destinations=destinations,
        carriers=carriers,
        coverage_signals=coverage,
    )


def _channels(folded: str) -> tuple[str, ...]:
    found: list[str] = []
    if re.search(r"\benvio\b|\benviar\b|\bcorreo\b", folded):
        found.append("DELIVERY")
    if re.search(r"\bmoto\b|\bcadete\b", folded):
        found.append("MOTORBIKE_COURIER")
    if re.search(r"\bcorreo\b", folded):
        found.append("POSTAL_COURIER")
    return tuple(dict.fromkeys(found))


def _destinations(folded: str) -> tuple[str, ...]:
    found: list[str] = []
    if re.search(r"\ba domicilio\b|\bdomicilio\b", folded):
        found.append("HOME")
    if re.search(r"\bsucursal\b", folded):
        found.append("BRANCH")
    if re.search(r"\bpunto hop\b|\bpunto de retiro\b|\bretiro\b", folded):
        found.append("PICKUP_POINT")
    return tuple(dict.fromkeys(found))


def _carriers(folded: str) -> tuple[str, ...]:
    found: list[str] = []
    if re.search(r"\bandreani\b", folded):
        found.append("ANDREANI")
    if re.search(r"\boca\b", folded):
        found.append("OCA")
    return tuple(found)


def _coverage_signals(folded: str) -> tuple[str, ...]:
    found: list[str] = []
    if re.search(r"\bdentro de\b.*\bcircunvalacion\b", folded):
        found.append("WITHIN_CIRCUNVALACION")
    if re.search(r"\bcordoba\b", folded):
        found.append("CORDOBA")
    return tuple(found)


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())
