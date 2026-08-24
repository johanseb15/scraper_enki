from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata


class ChargedUnitMeaning(str, Enum):
    HOUR = "HOUR"
    VISIT = "VISIT"
    UNIT = "UNIT"
    PROJECT = "PROJECT"
    TOTAL = "TOTAL"
    UNKNOWN = "UNKNOWN"


class BillingPeriodMeaning(str, Enum):
    MONTH = "MONTH"
    UNKNOWN = "UNKNOWN"


class PriceBoundMeaning(str, Enum):
    EXACT = "EXACT"
    FROM = "FROM"
    RANGE = "RANGE"
    MINIMUM = "MINIMUM"
    QUOTE_REQUIRED = "QUOTE_REQUIRED"
    UNKNOWN = "UNKNOWN"


class ScopeEpistemicStatus(str, Enum):
    EXPLICIT = "EXPLICIT"
    UNKNOWN = "UNKNOWN"


class ScopeCompatibility(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class PriceScopeMeaning:
    charged_unit: ChargedUnitMeaning = ChargedUnitMeaning.UNKNOWN
    billing_period: BillingPeriodMeaning = BillingPeriodMeaning.UNKNOWN
    price_bound: PriceBoundMeaning = PriceBoundMeaning.UNKNOWN
    status: ScopeEpistemicStatus = ScopeEpistemicStatus.UNKNOWN
    raw_basis: str | None = None
    provenance: str = "UNKNOWN"

    @property
    def comparison_scope(self) -> str:
        if self.billing_period is BillingPeriodMeaning.MONTH:
            return "PER_MONTH"
        return {
            ChargedUnitMeaning.HOUR: "PER_HOUR",
            ChargedUnitMeaning.VISIT: "PER_VISIT",
            ChargedUnitMeaning.UNIT: "PER_UNIT",
            ChargedUnitMeaning.PROJECT: "PER_PROJECT",
            ChargedUnitMeaning.TOTAL: "FIXED_TOTAL",
        }.get(self.charged_unit, "UNKNOWN")


def normalize_price_scope(
    raw_text: str,
    *,
    has_price: bool,
    is_range: bool = False,
    provenance: str = "raw_user_input",
) -> PriceScopeMeaning:
    text = _fold(raw_text)
    unit, unit_match = _charged_unit(text)
    billing, billing_match = _billing_period(text)
    bound, bound_match = _price_bound(text, has_price=has_price, is_range=is_range)
    markers = [item for item in (unit_match, billing_match, bound_match) if item]
    explicit_scope = unit is not ChargedUnitMeaning.UNKNOWN or billing is not BillingPeriodMeaning.UNKNOWN
    explicit_bound = bound in {
        PriceBoundMeaning.FROM,
        PriceBoundMeaning.MINIMUM,
        PriceBoundMeaning.RANGE,
        PriceBoundMeaning.QUOTE_REQUIRED,
    }
    return PriceScopeMeaning(
        charged_unit=unit, billing_period=billing, price_bound=bound,
        status=ScopeEpistemicStatus.EXPLICIT if explicit_scope or explicit_bound else ScopeEpistemicStatus.UNKNOWN,
        raw_basis=" | ".join(markers) or None, provenance=provenance,
    )


def compare_price_scopes(left: PriceScopeMeaning | str, right: PriceScopeMeaning | str) -> ScopeCompatibility:
    left_value = left.comparison_scope if isinstance(left, PriceScopeMeaning) else left
    right_value = right.comparison_scope if isinstance(right, PriceScopeMeaning) else right
    if left_value == "UNKNOWN" or right_value == "UNKNOWN":
        return ScopeCompatibility.INSUFFICIENT_EVIDENCE
    return ScopeCompatibility.COMPATIBLE if left_value == right_value else ScopeCompatibility.INCOMPATIBLE


def project_price_scope_dimension(scope: PriceScopeMeaning) -> str | None:
    if scope.comparison_scope != "UNKNOWN":
        return scope.comparison_scope
    if scope.price_bound in {PriceBoundMeaning.FROM, PriceBoundMeaning.MINIMUM}:
        return "LOWER_BOUND"
    if scope.price_bound is PriceBoundMeaning.RANGE:
        return "RANGE"
    return None


def comparison_scope_from_charged_unit(value: str) -> str | None:
    try:
        unit = ChargedUnitMeaning(value)
    except ValueError:
        return None
    result = PriceScopeMeaning(charged_unit=unit).comparison_scope
    return None if result == "UNKNOWN" else result


def _charged_unit(text):
    patterns = (
        (
            ChargedUnitMeaning.HOUR,
            r"\b(?:por\s+hora|la\s+hora|x\s*1\s*(?:hs?|hora)"
            r"|hora\s+(?:inicial|adicional|servicio|tecnica|tecnico)"
            r"|hora(?:s)?\s+de\s+(?:servicio|soporte|trabajo))\b",
        ),
        (ChargedUnitMeaning.VISIT, r"\b(?:por\s+visita|cada\s+visita)\b"),
        (
            ChargedUnitMeaning.UNIT,
            r"\b(?:por\s+(?:equipo|unidad|pc|notebook|camara)"
            r"|precios?\s+por\s+equipo"
            r"|cada\s+\d+(?:[.,]\d+)?\s*(?:gb|tb))\b",
        ),
        (ChargedUnitMeaning.PROJECT, r"\bpor\s+proyecto\b"),
        (ChargedUnitMeaning.TOTAL, r"\b(?:precio\s+(?:cerrado|total)|total\s+final)\b"),
    )
    for value, pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return value, match.group(0)
    return ChargedUnitMeaning.UNKNOWN, None


def _billing_period(text):
    match = re.search(r"\b(?:por\s+mes|al\s+mes|mensual(?:mente)?|abono\s+mensual)\b", text)
    return (BillingPeriodMeaning.MONTH, match.group(0)) if match else (BillingPeriodMeaning.UNKNOWN, None)


def _price_bound(text, *, has_price, is_range):
    match = re.search(r"\b(?:desde|a\s+partir\s+de)\b", text)
    if match:
        return PriceBoundMeaning.FROM, match.group(0)
    match = re.search(r"\b(?:precio\s+minimo|minimo)\b", text)
    if match:
        return PriceBoundMeaning.MINIMUM, match.group(0)
    match = re.search(r"\b(?:presupuesto(?:\s+a)?\s+consultar|consultar\s+precio)\b", text)
    if match:
        return PriceBoundMeaning.QUOTE_REQUIRED, match.group(0)
    match = re.search(r"\b(?:precio\s+(?:cerrado|exacto|total)|total\s+final)\b", text)
    if match:
        return PriceBoundMeaning.EXACT, match.group(0)
    if is_range:
        return PriceBoundMeaning.RANGE, "range price expression"
    return (PriceBoundMeaning.EXACT, None) if has_price else (PriceBoundMeaning.UNKNOWN, None)


def _fold(text):
    normalized = unicodedata.normalize("NFKD", text or "")
    return " ".join("".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().split())
