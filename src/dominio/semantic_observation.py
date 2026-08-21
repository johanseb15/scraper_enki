from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.dominio.semantic_knowledge import KnowledgeProvenance, SemanticContext


class SemanticObservationRole(Enum):
    SINGLE_SERVICE = "SINGLE_SERVICE"
    COMPOSITE_SERVICE = "COMPOSITE_SERVICE"
    SCOPE_DEVICE = "SCOPE_DEVICE"
    PRICE_CONTEXT = "PRICE_CONTEXT"
    NON_OBJECT = "NON_OBJECT"
    HARDWARE_PRODUCT = "HARDWARE_PRODUCT"
    LOGISTICS_CONTEXT = "LOGISTICS_CONTEXT"
    UNMAPPED = "UNMAPPED"


class ObservationUnderstandingStatus(Enum):
    FULLY_REPRESENTED = "FULLY_REPRESENTED"
    CLASSIFIED_ONLY = "CLASSIFIED_ONLY"
    PARTIALLY_UNDERSTOOD = "PARTIALLY_UNDERSTOOD"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"
    UNREPRESENTED = "UNREPRESENTED"


class PriceContextKind(Enum):
    TICKET_TIER = "TICKET_TIER"
    PRICE_CHANGE = "PRICE_CHANGE"
    ADDITIONAL_CHARGE = "ADDITIONAL_CHARGE"
    PAYMENT_DISCOUNT = "PAYMENT_DISCOUNT"
    PAYMENT_SPECIFIC_PRICE = "PAYMENT_SPECIFIC_PRICE"
    QUANTITY_PRICE_TABLE = "QUANTITY_PRICE_TABLE"
    TURNAROUND_TIME = "TURNAROUND_TIME"
    UNKNOWN = "UNKNOWN"


class PriceContextUnderstandingStatus(Enum):
    UNDERSTOOD = "PRICE_CONTEXT_UNDERSTOOD"
    PARTIAL = "PRICE_CONTEXT_PARTIAL"
    UNKNOWN = "PRICE_CONTEXT_UNKNOWN"


class ScopeMeaningKind(Enum):
    DEVICE_PROFILE = "DEVICE_PROFILE"
    TIER_ONLY = "TIER_ONLY"
    DATA_CAPACITY_BAND = "DATA_CAPACITY_BAND"
    PROVIDER_DELIVERY_CONTEXT = "PROVIDER_DELIVERY_CONTEXT"
    UNKNOWN = "UNKNOWN"


class ScopeUnderstandingStatus(Enum):
    UNDERSTOOD = "SCOPE_UNDERSTOOD"
    PARTIAL = "SCOPE_PARTIAL"
    UNKNOWN = "SCOPE_UNKNOWN"


class HardwareMeaningKind(Enum):
    SINGLE_COMPONENT_FAMILY = "SINGLE_COMPONENT_FAMILY"
    MULTI_COMPONENT_SYSTEM = "MULTI_COMPONENT_SYSTEM"
    SERVICE_LIKE_CONFLICT = "SERVICE_LIKE_CONFLICT"
    UNKNOWN = "UNKNOWN"


class HardwareUnderstandingStatus(Enum):
    UNDERSTOOD = "HARDWARE_UNDERSTOOD"
    PARTIAL = "HARDWARE_PARTIAL"
    AMBIGUOUS = "HARDWARE_AMBIGUOUS"
    UNKNOWN = "HARDWARE_UNKNOWN"

@dataclass(frozen=True)
class SemanticObservation:
    observation_id: str
    raw_expression: str
    semantic_role: SemanticObservationRole
    market_scope: str
    source: str
    provider: str
    province: str | None
    observation_provenance: KnowledgeProvenance
    interpretation_provenance: KnowledgeProvenance
    canonical_service: str | None = None
    matched_services: tuple[str, ...] = ()
    context: SemanticContext = SemanticContext.PROVIDER_OBSERVATION

    def __post_init__(self) -> None:
        if not self.observation_id or not self.observation_id.strip():
            raise ValueError("SemanticObservation requires observation_id.")
        if not self.raw_expression or not self.raw_expression.strip():
            raise ValueError("SemanticObservation requires raw_expression.")
        if self.observation_provenance is None:
            raise ValueError("SemanticObservation requires observation_provenance.")
        if self.interpretation_provenance is None:
            raise ValueError("SemanticObservation requires interpretation_provenance.")
        if self.canonical_service and self.semantic_role is not SemanticObservationRole.SINGLE_SERVICE:
            raise ValueError("Only SINGLE_SERVICE observations may carry canonical_service.")

    @property
    def understanding_status(self) -> ObservationUnderstandingStatus:
        if self.semantic_role is SemanticObservationRole.UNMAPPED:
            return ObservationUnderstandingStatus.UNKNOWN
        if self.semantic_role is SemanticObservationRole.SINGLE_SERVICE:
            if self.canonical_service:
                return ObservationUnderstandingStatus.FULLY_REPRESENTED
            return ObservationUnderstandingStatus.AMBIGUOUS
        if self.semantic_role is SemanticObservationRole.COMPOSITE_SERVICE:
            if self.matched_services:
                return ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD
            return ObservationUnderstandingStatus.CLASSIFIED_ONLY
        return ObservationUnderstandingStatus.CLASSIFIED_ONLY

@dataclass(frozen=True)
class PriceContextMeaning:
    source_expression: str
    context_kind: PriceContextKind
    provenance: KnowledgeProvenance
    price_scope: str = "UNKNOWN"
    published_currency: str = "UNKNOWN"
    raw_currency_markers: tuple[str, ...] = ()
    percent_value: float | None = None
    quantity_unit: str | None = None

    def __post_init__(self) -> None:
        if not self.source_expression or not self.source_expression.strip():
            raise ValueError("PriceContextMeaning requires source_expression.")
        if self.provenance is None:
            raise ValueError("PriceContextMeaning requires provenance.")

    @property
    def understanding_status(self) -> PriceContextUnderstandingStatus:
        if self.context_kind is PriceContextKind.UNKNOWN and self.price_scope == "UNKNOWN":
            return PriceContextUnderstandingStatus.UNKNOWN
        if self.price_scope == "UNKNOWN":
            return PriceContextUnderstandingStatus.PARTIAL
        return PriceContextUnderstandingStatus.UNDERSTOOD

@dataclass(frozen=True)
class ScopeMeaning:
    source_expression: str
    meaning_kind: ScopeMeaningKind
    provenance: KnowledgeProvenance
    device_types: tuple[str, ...] = ()
    tiers: tuple[str, ...] = ()
    capacity_max_value: float | None = None
    capacity_unit: str | None = None
    delivery_modes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_expression or not self.source_expression.strip():
            raise ValueError("ScopeMeaning requires source_expression.")
        if self.provenance is None:
            raise ValueError("ScopeMeaning requires provenance.")
        if self.capacity_max_value is not None and self.capacity_max_value <= 0:
            raise ValueError("ScopeMeaning capacity_max_value must be positive.")
        if self.capacity_max_value is not None and not self.capacity_unit:
            raise ValueError("ScopeMeaning capacity requires capacity_unit.")
        if self.capacity_unit and self.capacity_max_value is None:
            raise ValueError("ScopeMeaning capacity_unit requires capacity_max_value.")

    @property
    def understanding_status(self) -> ScopeUnderstandingStatus:
        if self.meaning_kind is ScopeMeaningKind.UNKNOWN:
            return ScopeUnderstandingStatus.UNKNOWN
        if self.meaning_kind is ScopeMeaningKind.DEVICE_PROFILE:
            return ScopeUnderstandingStatus.UNDERSTOOD if self.device_types else ScopeUnderstandingStatus.PARTIAL
        if self.meaning_kind is ScopeMeaningKind.TIER_ONLY:
            return ScopeUnderstandingStatus.UNDERSTOOD if self.tiers else ScopeUnderstandingStatus.PARTIAL
        if self.meaning_kind is ScopeMeaningKind.DATA_CAPACITY_BAND:
            return ScopeUnderstandingStatus.UNDERSTOOD if self.capacity_max_value is not None and self.capacity_unit else ScopeUnderstandingStatus.PARTIAL
        if self.meaning_kind is ScopeMeaningKind.PROVIDER_DELIVERY_CONTEXT:
            return ScopeUnderstandingStatus.UNDERSTOOD if self.delivery_modes else ScopeUnderstandingStatus.PARTIAL
        return ScopeUnderstandingStatus.PARTIAL

@dataclass(frozen=True)
class HardwareMeaning:
    source_expression: str
    meaning_kind: HardwareMeaningKind
    provenance: KnowledgeProvenance
    families: tuple[str, ...] = ()
    brand_signals: tuple[str, ...] = ()
    variant_signals: tuple[str, ...] = ()
    spec_signals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_expression or not self.source_expression.strip():
            raise ValueError("HardwareMeaning requires source_expression.")
        if self.provenance is None:
            raise ValueError("HardwareMeaning requires provenance.")

    @property
    def understanding_status(self) -> HardwareUnderstandingStatus:
        if self.meaning_kind is HardwareMeaningKind.UNKNOWN:
            return HardwareUnderstandingStatus.UNKNOWN
        if self.meaning_kind is HardwareMeaningKind.SERVICE_LIKE_CONFLICT:
            return HardwareUnderstandingStatus.AMBIGUOUS
        if self.meaning_kind is HardwareMeaningKind.SINGLE_COMPONENT_FAMILY:
            return (
                HardwareUnderstandingStatus.UNDERSTOOD
                if len(self.families) == 1
                else HardwareUnderstandingStatus.PARTIAL
            )
        if self.meaning_kind is HardwareMeaningKind.MULTI_COMPONENT_SYSTEM:
            return (
                HardwareUnderstandingStatus.UNDERSTOOD
                if len(self.families) >= 2
                else HardwareUnderstandingStatus.PARTIAL
            )
        return HardwareUnderstandingStatus.PARTIAL
