from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from collections.abc import Mapping
import re
import unicodedata


COMMERCIAL_CONTEXT_VERSION = "commercial-context-v1"


class CommercialContextValue(str, Enum):
    STANDARD = "STANDARD"
    URGENCY = "URGENCY"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class CommercialContextOrigin(str, Enum):
    USER_CLAIM = "USER_CLAIM"
    SOURCE_CLAIM = "SOURCE_CLAIM"
    COHORT_ARTIFACT = "COHORT_ARTIFACT"
    CONTROLLED_FIXTURE = "CONTROLLED_FIXTURE"
    UNKNOWN = "UNKNOWN"


class CommercialContextCompatibility(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    MISMATCH = "MISMATCH"
    UNKNOWN_SIDE = "UNKNOWN_SIDE"
    AMBIGUOUS_SIDE = "AMBIGUOUS_SIDE"


class PartsScope(str, Enum):
    LABOR_ONLY = "LABOR_ONLY"
    PARTS_INCLUDED = "PARTS_INCLUDED"
    USER_PROVIDED = "USER_PROVIDED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CommercialContext:
    value: CommercialContextValue = CommercialContextValue.UNKNOWN
    origin: CommercialContextOrigin = CommercialContextOrigin.UNKNOWN
    raw_basis: tuple[str, ...] = ()
    resolution_method: str = COMMERCIAL_CONTEXT_VERSION
    parts_scope: PartsScope = PartsScope.UNKNOWN
    quantity: int | None = None
    environment: str = "UNKNOWN"
    payment_method: str = "UNKNOWN"

    @property
    def urgency(self) -> str:
        """Brownfield read compatibility; the canonical identity is ``value``."""
        return self.value.value

    @property
    def status(self) -> str:
        if self.value is CommercialContextValue.UNKNOWN:
            return "UNKNOWN"
        if self.value is CommercialContextValue.AMBIGUOUS:
            return "AMBIGUOUS"
        return "OBSERVED"

    def with_parts_scope(self, parts_scope: PartsScope) -> CommercialContext:
        return replace(self, parts_scope=parts_scope)


_URGENCY_PATTERN = re.compile(
    r"\burgenc(?:ia|ias)\b|\burgente\b|\bemergenc(?:ia|ias)\b"
    r"|\bfuera\s+de\s+horario\b|\bfin(?:es)?\s+de\s+semana\b"
    r"|\bferiado(?:s)?\b"
)
_STANDARD_PATTERN = re.compile(
    r"\bsin\s+urgencia\b|\bhorario\s+(?:habitual|normal|comercial)\b"
    r"|\b(?:servicio|soporte(?:\s+remoto)?)\s+(?:habitual|normal|standard|estandar)\b"
    r"|\bcontexto\s+(?:standard|estandar)\b"
)


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).lower()


def resolve_commercial_context(
    raw_text: str,
    *,
    origin: CommercialContextOrigin,
) -> CommercialContext:
    """Resolve once from one claim while preserving its origin and raw basis."""
    folded = _fold(raw_text)
    urgency = tuple(match.group(0) for match in _URGENCY_PATTERN.finditer(folded))
    standard = tuple(match.group(0) for match in _STANDARD_PATTERN.finditer(folded))
    basis = tuple(dict.fromkeys((*standard, *urgency)))
    if urgency and standard:
        value = CommercialContextValue.AMBIGUOUS
    elif urgency:
        value = CommercialContextValue.URGENCY
    elif standard:
        value = CommercialContextValue.STANDARD
    else:
        value = CommercialContextValue.UNKNOWN
    return CommercialContext(value=value, origin=origin, raw_basis=basis)


def commercial_context_from_value(
    value: str | CommercialContextValue | CommercialContext | Mapping[str, object] | None,
    *,
    origin: CommercialContextOrigin,
    raw_basis: tuple[str, ...] = (),
) -> CommercialContext:
    if isinstance(value, CommercialContext):
        return value
    if isinstance(value, Mapping):
        mapped_value = value.get("value")
        mapped_origin = value.get("origin")
        mapped_parts = value.get("parts_scope")
        return CommercialContext(
            value=mapped_value
            if isinstance(mapped_value, CommercialContextValue)
            else CommercialContextValue(str(mapped_value or "UNKNOWN")),
            origin=mapped_origin
            if isinstance(mapped_origin, CommercialContextOrigin)
            else origin,
            raw_basis=tuple(str(item) for item in value.get("raw_basis", ()) or ()),
            resolution_method=str(
                value.get("resolution_method") or COMMERCIAL_CONTEXT_VERSION
            ),
            parts_scope=mapped_parts
            if isinstance(mapped_parts, PartsScope)
            else PartsScope(str(mapped_parts or "UNKNOWN")),
            quantity=value.get("quantity") if isinstance(value.get("quantity"), int) else None,
            environment=str(value.get("environment") or "UNKNOWN"),
            payment_method=str(value.get("payment_method") or "UNKNOWN"),
        )
    normalized = str(value or "UNKNOWN").strip().upper() or "UNKNOWN"
    try:
        canonical = CommercialContextValue(normalized)
    except ValueError as exc:
        raise ValueError(f"Unsupported commercial context: {value!r}") from exc
    return CommercialContext(value=canonical, origin=origin, raw_basis=raw_basis)


def compare_commercial_contexts(
    left: CommercialContext,
    right: CommercialContext,
) -> CommercialContextCompatibility:
    if CommercialContextValue.AMBIGUOUS in {left.value, right.value}:
        return CommercialContextCompatibility.AMBIGUOUS_SIDE
    if CommercialContextValue.UNKNOWN in {left.value, right.value}:
        return CommercialContextCompatibility.UNKNOWN_SIDE
    if left.value is right.value:
        return CommercialContextCompatibility.COMPATIBLE
    return CommercialContextCompatibility.MISMATCH


def serialize_commercial_context(context: CommercialContext) -> dict[str, object]:
    return {
        "value": context.value.value,
        "status": context.status,
        "origin": context.origin.value,
        "raw_basis": list(context.raw_basis),
        "resolution_method": context.resolution_method,
    }
