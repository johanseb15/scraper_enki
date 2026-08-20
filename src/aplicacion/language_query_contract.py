from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class QueryKind(str, Enum):
    ECONOMIC_QUERY="ECONOMIC_QUERY"; TECHNICAL_NEED="TECHNICAL_NEED"; UNKNOWN="UNKNOWN"
class IntentAction(str, Enum):
    EVALUATE_PRICE="EVALUATE_PRICE"; SUGGEST_PRICE="SUGGEST_PRICE"; MARKET_REFERENCE="MARKET_REFERENCE"; COMPARE="COMPARE"; UNKNOWN="UNKNOWN"
class IntentSide(str, Enum):
    BUY="BUY"; SELL="SELL"; NEUTRAL="NEUTRAL"; UNKNOWN="UNKNOWN"
class EconomicObjectKind(str, Enum):
    SERVICE="SERVICE"; HARDWARE="HARDWARE"; BUNDLE="BUNDLE"; DIGITAL_GOOD="DIGITAL_GOOD"; UNKNOWN="UNKNOWN"
class MarketScope(str, Enum):
    LOCAL="LOCAL"; REMOTE_NATIONAL="REMOTE_NATIONAL"; GOODS="GOODS"; DIGITAL="DIGITAL"; UNKNOWN="UNKNOWN"
class ServiceModality(str, Enum):
    WORKSHOP="WORKSHOP"; ONSITE="ONSITE"; REMOTE="REMOTE"; UNKNOWN="UNKNOWN"
class PriceType(str, Enum):
    EXACT="EXACT"; RANGE="RANGE"; MIN="MIN"; MAX="MAX"; PER_HOUR="PER_HOUR"; PER_MONTH="PER_MONTH"; PER_UNIT="PER_UNIT"; PER_VISIT="PER_VISIT"; PER_PROJECT="PER_PROJECT"; UNKNOWN="UNKNOWN"
class PartsScope(str, Enum):
    LABOR_ONLY="LABOR_ONLY"; PARTS_INCLUDED="PARTS_INCLUDED"; USER_PROVIDED="USER_PROVIDED"; UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class PriceMention:
    type: PriceType=PriceType.UNKNOWN
    value: float|None=None
    min: float|None=None
    max: float|None=None
    currency: str="UNKNOWN"
    raw_expression: str|None=None
    is_approximate: bool=False

@dataclass(frozen=True)
class Geography:
    raw_location: str|None=None
    province: str|None=None
    city: str|None=None

@dataclass(frozen=True)
class CommercialContext:
    parts_scope: PartsScope=PartsScope.UNKNOWN
    quantity: int|None=None
    urgency: str="UNKNOWN"
    environment: str="UNKNOWN"
    payment_method: str="UNKNOWN"

@dataclass(frozen=True)
class ParseMetadata:
    confidence: float
    clarification_required: bool
    clarification_reason: str|None=None
    clarification_question: str|None=None
    explicit_fields: tuple[str,...]=()
    inferred_fields: tuple[str,...]=()
    derived_fields: tuple[str,...]=()

@dataclass(frozen=True)
class TechnicalNeed:
    domain: str="UNKNOWN"
    technical_problem: str="UNKNOWN"
    economic_intent_explicit: bool=False
    candidate_routes: tuple[str,...]=()
    product_purchase_recommendation: str="NONE_YET"
    clarification_required: bool=True

@dataclass(frozen=True)
class ParsedPricingQuery:
    raw_text: str
    normalized_text: str
    intent_action: IntentAction
    intent_side: IntentSide
    economic_object_kind: EconomicObjectKind
    canonical_services: tuple[str,...]
    market_scope: MarketScope
    modality: ServiceModality
    price: PriceMention
    geography: Geography
    device_type: str|None=None
    condition: str="UNKNOWN"
    is_bundle: bool=False
    commercial_context: CommercialContext=field(default_factory=CommercialContext)
    metadata: ParseMetadata=field(default_factory=lambda: ParseMetadata(0.0, True))
    language_evidence_type: str="UNKNOWN"
    query_kind: QueryKind=QueryKind.ECONOMIC_QUERY
    technical_need: TechnicalNeed|None=None
