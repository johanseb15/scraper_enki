from __future__ import annotations

import re
import unicodedata

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

    if _looks_like_service_action(folded):
        return HardwareMeaning(
            source_expression=raw,
            meaning_kind=HardwareMeaningKind.SERVICE_LIKE_CONFLICT,
            provenance=observation.interpretation_provenance,
            families=_families(folded),
            brand_signals=_brand_signals(folded),
            variant_signals=_variant_signals(folded),
            spec_signals=_spec_signals(folded),
        )

    families = _families(folded)
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
        brand_signals=_brand_signals(folded),
        variant_signals=_variant_signals(folded),
        spec_signals=_spec_signals(folded),
    )


def _looks_like_service_action(folded: str) -> bool:
    return bool(
        re.search(
            r"\b(?:cambio|cambiar|reemplazo|reemplazar|instalacion|instalar|"
            r"reparacion|reparar|upgrade|ampliacion)\b",
            folded,
        )
    )


def _families(folded: str) -> tuple[str, ...]:
    found: list[str] = []

    if re.search(
        r"\b(?:cpu|procesador|ryzen(?:\s+[3579])?|core\s+i[3579]|i[3579]\s*\d{3,5})\b",
        folded,
    ):
        found.append("CPU")

    if re.search(
        r"\b(?:gpu|placa(?:s)? de video|rtx\s*\d{3,4}|gtx\s*\d{3,4}|"
        r"rx\s*\d{3,4}|6700xt|1660(?:\s+ti|\s+super)?)\b",
        folded,
    ):
        found.append("GPU")

    if re.search(r"\b(?:ram|memoria ram|ddr[345])\b", folded):
        found.append("MEMORY")

    if re.search(
        r"\b(?:ssd|nvme|hdd|m\.?2|storage|disco|disco rigido|disco duro)\b",
        folded,
    ):
        found.append("STORAGE")

    if re.search(r"\b(?:fuente|psu)\b", folded):
        found.append("PSU")

    if re.search(r"\b(?:notebook|laptop)\b", folded):
        found.append("NOTEBOOK")

    return tuple(dict.fromkeys(found))


def _brand_signals(folded: str) -> tuple[str, ...]:
    brands = (
        "AMD",
        "INTEL",
        "NVIDIA",
        "ASROCK",
        "ASUS",
        "MSI",
        "GIGABYTE",
        "EVGA",
        "ZOTAC",
        "XFX",
        "KINGSTON",
        "CORSAIR",
        "SEAGATE",
    )
    return tuple(
        brand for brand in brands if re.search(rf"\b{brand.lower()}\b", folded)
    )


def _variant_signals(folded: str) -> tuple[str, ...]:
    found: list[str] = []
    for pattern, label in (
        (r"\bgamer\b|\bgaming\b", "GAMING"),
        (r"\bti\b", "TI"),
        (r"\bsuper\b", "SUPER"),
        (r"\boc\b", "OC"),
        (r"\bultra\b", "ULTRA"),
        (r"\bentrada\b", "ENTRY"),
        (r"\bmedia\b", "MID"),
        (r"\balta\b", "HIGH"),
    ):
        if re.search(pattern, folded):
            found.append(label)
    return tuple(dict.fromkeys(found))


def _spec_signals(folded: str) -> tuple[str, ...]:
    found: list[str] = []
    for pattern in (
        r"\b\d+(?:[.,]\d+)?\s*gb\b",
        r"\b\d+(?:[.,]\d+)?\s*tb\b",
        r"\bddr[345]\b",
        r"\b\d+\s*w\b",
    ):
        for match in re.finditer(pattern, folded):
            found.append(match.group(0).upper())
    return tuple(dict.fromkeys(found))


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())
