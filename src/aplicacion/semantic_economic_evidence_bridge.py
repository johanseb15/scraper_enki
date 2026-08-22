from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from src.dominio.economic_evidence import (
    EconomicEvidenceContext,
    EconomicEvidenceDimensionsV2,
    EconomicEvidenceRecord,
    EconomicObjectKind,
    EconomicReadiness,
    DimensionStatus,
    EvidenceExclusionReason,
    ExcludedEconomicEvidence,
)
from src.dominio.semantic_observation import (
    HardwareMeaning,
    HardwareMeaningKind,
    ObservationUnderstandingStatus,
    SemanticObservationRole,
)
from src.dominio.semantic_understanding import SemanticUnderstandingEnvelope


_CONTEXT_REASON = {
    SemanticObservationRole.PRICE_CONTEXT: EvidenceExclusionReason.PRICE_CONTEXT_ONLY,
    SemanticObservationRole.SCOPE_DEVICE: EvidenceExclusionReason.SCOPE_ONLY,
    SemanticObservationRole.NON_OBJECT: EvidenceExclusionReason.NON_ECONOMIC_OBJECT,
    SemanticObservationRole.LOGISTICS_CONTEXT: EvidenceExclusionReason.LOGISTICS_ONLY,
    SemanticObservationRole.UNMAPPED: EvidenceExclusionReason.UNKNOWN_SEMANTICS,
}


class SemanticEconomicEvidenceBridge:
    """Read-only semantic-to-economic resolver; it never mutates pricing runtime."""

    def __init__(self, evidence: Iterable[EconomicEvidenceRecord]) -> None:
        self._evidence = tuple(evidence)
        ids = [item.evidence_id for item in self._evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("Economic evidence ids must be unique.")
        self._evidence_by_id = {item.evidence_id: item for item in self._evidence}
        role_groups = {
            role: tuple(item for item in self._evidence if item.semantic_role is role)
            for role in SemanticObservationRole
        }
        economic_roles = {
            SemanticObservationRole.SINGLE_SERVICE,
            SemanticObservationRole.COMPOSITE_SERVICE,
            SemanticObservationRole.HARDWARE_PRODUCT,
        }
        economic_pool = tuple(
            item for item in self._evidence if item.semantic_role in economic_roles
        )
        self._candidate_pools = {
            role: (economic_pool if role in economic_roles else role_groups[role])
            for role in SemanticObservationRole
        }
        self._candidate_pairs_before = 0
        self._candidate_pairs_after = 0
        self._candidate_results = 0

    @property
    def candidate_generation_metrics(self) -> dict[str, int]:
        return {
            "CANDIDATE_PAIRS_BEFORE_INDEX": self._candidate_pairs_before,
            "CANDIDATE_PAIRS_AFTER_INDEX": self._candidate_pairs_after,
            "CANDIDATE_RESULTS": self._candidate_results,
        }

    def resolve(self, envelope: SemanticUnderstandingEnvelope) -> EconomicEvidenceContext:
        observation = envelope.observation
        anchor = self._evidence_by_id.get(observation.observation_id)
        if observation.semantic_role in _CONTEXT_REASON:
            pool = (anchor,) if anchor is not None else ()
        else:
            pool = self._candidate_pools[observation.semantic_role]
        self._candidate_pairs_before += len(self._evidence)
        self._candidate_pairs_after += len(pool)
        candidates = tuple(
            item for item in pool
            if self._is_candidate(
                observation.semantic_role,
                observation.observation_id,
                item,
            )
        )
        self._candidate_results += len(candidates)
        excluded: list[ExcludedEconomicEvidence] = []
        comparable: list[EconomicEvidenceRecord] = []
        for item in candidates:
            reasons = self._exclusion_reasons(envelope, anchor, item)
            if (
                item.evidence_id == observation.observation_id
                and observation.semantic_role not in _CONTEXT_REASON
            ):
                reasons = _unique([
                    *reasons,
                    EvidenceExclusionReason.SELF_OBSERVATION_NOT_INDEPENDENT,
                ])
            if reasons:
                excluded.append(ExcludedEconomicEvidence(item, reasons))
            else:
                comparable.append(item)

        missing = self._missing_dimensions(envelope, anchor, comparable)
        readiness = self._readiness(envelope, comparable, missing)
        providers = len({value for item in comparable if (value := _provider_identity(item))})
        conflicted_dimensions = _conflicted_dimensions(anchor)
        uncertainty = tuple(
            value for value in (
                envelope.status.value if envelope.status in {
                    ObservationUnderstandingStatus.UNKNOWN,
                    ObservationUnderstandingStatus.AMBIGUOUS,
                    ObservationUnderstandingStatus.UNREPRESENTED,
                } else None,
                "SOURCE_EVIDENCE_ROW_NOT_FOUND" if anchor is None else None,
            ) if value
        )
        return EconomicEvidenceContext(
            observation_id=observation.observation_id,
            economic_object_kind=_economic_object_kind(observation.semantic_role),
            semantic_role=observation.semantic_role,
            understanding_status=envelope.status,
            canonical_service=observation.canonical_service,
            matched_services=observation.matched_services,
            candidate_evidence=candidates,
            comparable_evidence=tuple(comparable),
            excluded_evidence=tuple(excluded),
            missing_dimensions=missing,
            readiness=readiness,
            evidence_count=len(comparable),
            independent_provider_count=providers,
            geography_scope=(
                _geography_scope(anchor)
                if anchor else observation.market_scope
            ) or "UNKNOWN",
            price_scope=(
                _dimension_value(anchor, "price_scope")
                if anchor else None
            ) or "UNKNOWN",
            provenance=(observation.observation_provenance, observation.interpretation_provenance),
            uncertainty=uncertainty,
            conflicted_dimensions=conflicted_dimensions,
        )

    @staticmethod
    def _is_candidate(
        role: SemanticObservationRole,
        observation_id: str,
        item: EconomicEvidenceRecord,
    ) -> bool:
        if role in _CONTEXT_REASON:
            return item.evidence_id == observation_id
        if role in {SemanticObservationRole.SINGLE_SERVICE, SemanticObservationRole.COMPOSITE_SERVICE}:
            return item.semantic_role in {
                SemanticObservationRole.SINGLE_SERVICE,
                SemanticObservationRole.COMPOSITE_SERVICE,
                SemanticObservationRole.HARDWARE_PRODUCT,
            }
        if role is SemanticObservationRole.HARDWARE_PRODUCT:
            return item.semantic_role in {
                SemanticObservationRole.HARDWARE_PRODUCT,
                SemanticObservationRole.SINGLE_SERVICE,
                SemanticObservationRole.COMPOSITE_SERVICE,
            }
        return True

    def _exclusion_reasons(
        self,
        envelope: SemanticUnderstandingEnvelope,
        anchor: EconomicEvidenceRecord | None,
        item: EconomicEvidenceRecord,
    ) -> tuple[EvidenceExclusionReason, ...]:
        role = envelope.observation.semantic_role
        conflict_reasons = []
        if _conflicted_dimensions(anchor) or _conflicted_dimensions(item):
            conflict_reasons.append(EvidenceExclusionReason.DIMENSION_CONFLICT)
        if envelope.status is ObservationUnderstandingStatus.UNKNOWN:
            return _unique([*conflict_reasons, EvidenceExclusionReason.UNKNOWN_SEMANTICS])
        if envelope.status is ObservationUnderstandingStatus.AMBIGUOUS:
            return _unique([*conflict_reasons, EvidenceExclusionReason.AMBIGUOUS_OBJECT])
        if role in _CONTEXT_REASON:
            return _unique([*conflict_reasons, _CONTEXT_REASON[role]])
        if role is SemanticObservationRole.COMPOSITE_SERVICE:
            return _unique([*conflict_reasons, EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE])
        if role is SemanticObservationRole.HARDWARE_PRODUCT:
            return _unique([*conflict_reasons, *self._hardware_reasons(envelope.meaning, anchor, item)])
        return _unique([*conflict_reasons, *self._service_reasons(envelope, anchor, item)])

    @staticmethod
    def _service_reasons(
        envelope: SemanticUnderstandingEnvelope,
        anchor: EconomicEvidenceRecord | None,
        item: EconomicEvidenceRecord,
    ) -> tuple[EvidenceExclusionReason, ...]:
        reasons: list[EvidenceExclusionReason] = []
        if item.semantic_role is SemanticObservationRole.HARDWARE_PRODUCT:
            return (EvidenceExclusionReason.HARDWARE_SERVICE_BOUNDARY,)
        if item.semantic_role is SemanticObservationRole.COMPOSITE_SERVICE:
            return (EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE,)
        if _dimension_value(item, "bundle_status") == "COMPOSITE":
            return (EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE,)
        if item.understanding_status in {
            ObservationUnderstandingStatus.UNKNOWN,
            ObservationUnderstandingStatus.UNREPRESENTED,
        }:
            reasons.append(EvidenceExclusionReason.UNKNOWN_SEMANTICS)
        if item.understanding_status is ObservationUnderstandingStatus.AMBIGUOUS:
            reasons.append(EvidenceExclusionReason.AMBIGUOUS_OBJECT)
        if item.canonical_service != envelope.observation.canonical_service:
            reasons.append(EvidenceExclusionReason.CANONICAL_SERVICE_MISMATCH)
        reasons.extend(_shared_dimension_reasons(anchor, item, require_geography=True))
        return _unique(reasons)

    @staticmethod
    def _hardware_reasons(
        target_meaning: object | None,
        anchor: EconomicEvidenceRecord | None,
        item: EconomicEvidenceRecord,
    ) -> tuple[EvidenceExclusionReason, ...]:
        if item.semantic_role is not SemanticObservationRole.HARDWARE_PRODUCT:
            return (EvidenceExclusionReason.HARDWARE_SERVICE_BOUNDARY,)
        if not isinstance(target_meaning, HardwareMeaning) or not isinstance(item.meaning, HardwareMeaning):
            return (EvidenceExclusionReason.UNKNOWN_SEMANTICS,)
        if target_meaning.meaning_kind is HardwareMeaningKind.SERVICE_LIKE_CONFLICT:
            return (EvidenceExclusionReason.AMBIGUOUS_OBJECT,)
        if (
            target_meaning.meaning_kind is HardwareMeaningKind.MULTI_COMPONENT_SYSTEM
            or item.meaning.meaning_kind is HardwareMeaningKind.MULTI_COMPONENT_SYSTEM
        ):
            return (EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE,)
        reasons: list[EvidenceExclusionReason] = []
        if set(target_meaning.families) != set(item.meaning.families):
            reasons.append(EvidenceExclusionReason.HARDWARE_FAMILY_MISMATCH)
        reasons.extend(_shared_dimension_reasons(anchor, item, require_geography=False))
        return _unique(reasons)

    @staticmethod
    def _missing_dimensions(
        envelope: SemanticUnderstandingEnvelope,
        anchor: EconomicEvidenceRecord | None,
        comparable: list[EconomicEvidenceRecord],
    ) -> tuple[str, ...]:
        missing: list[str] = []
        role = envelope.observation.semantic_role
        if role is SemanticObservationRole.SINGLE_SERVICE and not envelope.observation.canonical_service:
            missing.append("CANONICAL_SERVICE")
        if anchor is None:
            missing.append("SOURCE_EVIDENCE_ROW")
        else:
            if _dimension_value(anchor, "price_scope") in {None, "UNKNOWN"}:
                missing.append("PRICE_SCOPE")
            if _dimension_value(anchor, "currency") in {None, "UNKNOWN"}:
                missing.append("CURRENCY")
            if isinstance(anchor.dimensions, EconomicEvidenceDimensionsV2):
                if _dimension_value(anchor, "delivery_mode") is None:
                    missing.append("DELIVERY_MODE")
                if _dimension_value(anchor, "geographic_reach") is None:
                    missing.append("GEOGRAPHIC_REACH")
                if _dimension_value(anchor, "commercial_context") is None:
                    missing.append("COMMERCIAL_CONTEXT")
                if _dimension_value(anchor, "delivery_mode") == "ONSITE" and not _province(anchor):
                    missing.append("LOCATION")
            elif _dimension_value(anchor, "market_scope") == "LOCAL_SERVICE" and not _province(anchor):
                missing.append("GEOGRAPHY")
            for name in _conflicted_dimensions(anchor):
                missing.append(f"CONFLICTED_{name.upper()}")
        if role is SemanticObservationRole.COMPOSITE_SERVICE:
            missing.append("BUNDLE_DEFINITION")
        if role is SemanticObservationRole.HARDWARE_PRODUCT:
            meaning = envelope.meaning
            if not isinstance(meaning, HardwareMeaning) or not meaning.families:
                missing.append("HARDWARE_FAMILY")
            if isinstance(meaning, HardwareMeaning) and meaning.meaning_kind is HardwareMeaningKind.MULTI_COMPONENT_SYSTEM:
                missing.append("SYSTEM_SPECIFICATION")
        if not comparable:
            missing.append("COMPARABLE_EVIDENCE")
        return tuple(dict.fromkeys(missing))

    @staticmethod
    def _readiness(
        envelope: SemanticUnderstandingEnvelope,
        comparable: list[EconomicEvidenceRecord],
        missing: tuple[str, ...],
    ) -> EconomicReadiness:
        if envelope.status in {ObservationUnderstandingStatus.UNKNOWN, ObservationUnderstandingStatus.UNREPRESENTED}:
            return EconomicReadiness.UNKNOWN
        if envelope.status is ObservationUnderstandingStatus.AMBIGUOUS:
            return EconomicReadiness.AMBIGUOUS
        if any(name.startswith("CONFLICTED_") for name in missing):
            return EconomicReadiness.AMBIGUOUS
        if envelope.observation.semantic_role in _CONTEXT_REASON:
            return EconomicReadiness.INSUFFICIENT
        if envelope.observation.semantic_role is SemanticObservationRole.COMPOSITE_SERVICE:
            return EconomicReadiness.INSUFFICIENT
        meaning = envelope.meaning
        if isinstance(meaning, HardwareMeaning):
            if meaning.meaning_kind is HardwareMeaningKind.SERVICE_LIKE_CONFLICT:
                return EconomicReadiness.AMBIGUOUS
            if meaning.meaning_kind is HardwareMeaningKind.MULTI_COMPONENT_SYSTEM:
                return EconomicReadiness.INSUFFICIENT
        if any(name in missing for name in (
            "SOURCE_EVIDENCE_ROW", "PRICE_SCOPE", "CURRENCY", "GEOGRAPHY",
            "DELIVERY_MODE", "GEOGRAPHIC_REACH", "COMMERCIAL_CONTEXT", "LOCATION",
        )):
            return EconomicReadiness.INSUFFICIENT
        prices = [item.price_value for item in comparable if item.price_value is not None and item.price_value > 0]
        providers = len({value for item in comparable if (value := _provider_identity(item))})
        spread = (max(prices) / min(prices)) if prices else Decimal("Infinity")
        if len(comparable) >= 5 and providers >= 3 and spread <= Decimal("2.5"):
            return EconomicReadiness.READY
        if len(comparable) >= 3 and providers >= 2 and spread <= Decimal("2.0"):
            return EconomicReadiness.PARTIAL
        return EconomicReadiness.INSUFFICIENT


def _shared_dimension_reasons(
    anchor: EconomicEvidenceRecord | None,
    item: EconomicEvidenceRecord,
    *,
    require_geography: bool,
) -> list[EvidenceExclusionReason]:
    if anchor is None:
        return [EvidenceExclusionReason.INSUFFICIENT_SCOPE]
    if isinstance(anchor.dimensions, EconomicEvidenceDimensionsV2):
        if not isinstance(item.dimensions, EconomicEvidenceDimensionsV2):
            return [EvidenceExclusionReason.INSUFFICIENT_SCOPE]
        return _v2_shared_dimension_reasons(anchor, item)
    reasons: list[EvidenceExclusionReason] = []
    anchor_market = _dimension_value(anchor, "market_scope")
    item_market = _dimension_value(item, "market_scope")
    if not anchor_market or not item_market:
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
    elif anchor_market != item_market:
        reasons.append(EvidenceExclusionReason.MARKET_SCOPE_MISMATCH)
    elif require_geography and anchor_market == "LOCAL_SERVICE":
        anchor_province = _province(anchor)
        item_province = _province(item)
        if not anchor_province or not item_province:
            reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
        elif anchor_province != item_province:
            reasons.append(EvidenceExclusionReason.GEOGRAPHY_MISMATCH)
    anchor_currency = _dimension_value(anchor, "currency")
    item_currency = _dimension_value(item, "currency")
    if not anchor_currency or not item_currency:
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
    elif anchor_currency != item_currency:
        reasons.append(EvidenceExclusionReason.CURRENCY_MISMATCH)
    anchor_price_scope = _dimension_value(anchor, "price_scope")
    item_price_scope = _dimension_value(item, "price_scope")
    if not anchor_price_scope or not item_price_scope:
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
    elif anchor_price_scope != item_price_scope:
        reasons.append(EvidenceExclusionReason.CADENCE_MISMATCH)
    anchor_context = _dimension_value(anchor, "commercial_context")
    item_context = _dimension_value(item, "commercial_context")
    if (anchor_context is None) != (item_context is None):
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
    elif anchor_context is not None and anchor_context != item_context:
        reasons.append(EvidenceExclusionReason.COMMERCIAL_CONTEXT_MISMATCH)
    anchor_bundle = _dimension_value(anchor, "bundle_status")
    item_bundle = _dimension_value(item, "bundle_status")
    if item_bundle == "COMPOSITE" or anchor_bundle == "COMPOSITE":
        reasons.append(EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE)
    elif (anchor_bundle is None) != (item_bundle is None):
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
    _compare_optional_dimension(
        reasons,
        anchor,
        item,
        "device_scope",
        EvidenceExclusionReason.DEVICE_SCOPE_MISMATCH,
    )
    _compare_optional_dimension(
        reasons,
        anchor,
        item,
        "hardware_included",
        EvidenceExclusionReason.HARDWARE_INCLUDED_MISMATCH,
    )
    _compare_optional_dimension(
        reasons,
        anchor,
        item,
        "materials_included",
        EvidenceExclusionReason.MATERIALS_INCLUDED_MISMATCH,
    )
    if item.price_value is None or item.price_value <= 0:
        reasons.append(EvidenceExclusionReason.INVALID_PRICE)
    return reasons


def _v2_shared_dimension_reasons(
    anchor: EconomicEvidenceRecord,
    item: EconomicEvidenceRecord,
) -> list[EvidenceExclusionReason]:
    reasons: list[EvidenceExclusionReason] = []
    for name, mismatch_reason in (
        ("currency", EvidenceExclusionReason.CURRENCY_MISMATCH),
        ("price_scope", EvidenceExclusionReason.CADENCE_MISMATCH),
        ("delivery_mode", EvidenceExclusionReason.DELIVERY_MODE_MISMATCH),
        ("geographic_reach", EvidenceExclusionReason.GEOGRAPHIC_REACH_MISMATCH),
        ("commercial_context", EvidenceExclusionReason.COMMERCIAL_CONTEXT_MISMATCH),
    ):
        left = _dimension_value(anchor, name)
        right = _dimension_value(item, name)
        if left is None or right is None:
            reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
        elif left != right:
            reasons.append(mismatch_reason)

    anchor_bundle = _dimension_value(anchor, "bundle_status")
    item_bundle = _dimension_value(item, "bundle_status")
    if anchor_bundle == "COMPOSITE" or item_bundle == "COMPOSITE":
        reasons.append(EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE)
    elif anchor_bundle is None or item_bundle is None:
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
    elif anchor_bundle != item_bundle:
        reasons.append(EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE)

    _compare_optional_dimension(
        reasons, anchor, item, "device_scope",
        EvidenceExclusionReason.DEVICE_SCOPE_MISMATCH,
    )
    _compare_optional_dimension(
        reasons, anchor, item, "hardware_included",
        EvidenceExclusionReason.HARDWARE_INCLUDED_MISMATCH,
    )
    _compare_optional_dimension(
        reasons, anchor, item, "materials_included",
        EvidenceExclusionReason.MATERIALS_INCLUDED_MISMATCH,
    )
    if item.price_value is None or item.price_value <= 0:
        reasons.append(EvidenceExclusionReason.INVALID_PRICE)
    return reasons


def _compare_optional_dimension(
    reasons: list[EvidenceExclusionReason],
    anchor: EconomicEvidenceRecord,
    item: EconomicEvidenceRecord,
    name: str,
    mismatch: EvidenceExclusionReason,
) -> None:
    anchor_value = _dimension_value(anchor, name)
    item_value = _dimension_value(item, name)
    if anchor_value is not None and item_value is not None and anchor_value != item_value:
        reasons.append(mismatch)
    elif (anchor_value is None) != (item_value is None):
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)


def _dimension_value(item: EconomicEvidenceRecord, name: str):
    if item.dimensions is not None:
        dimension = item.dimensions.all_dimensions().get(name)
        if dimension is None:
            return None
        return dimension.value if dimension.is_usable else None
    legacy = {
        "market_scope": item.market_scope,
        "currency": item.currency,
        "price_scope": item.price_scope,
        "commercial_context": item.commercial_context,
    }
    value = legacy.get(name)
    return None if value in {None, "", "UNKNOWN"} else value


def _province(item: EconomicEvidenceRecord) -> str | None:
    if item.dimensions is not None:
        dimensions = item.dimensions.all_dimensions()
        location = dimensions.get("location") or dimensions.get("geography")
        if location is not None and location.is_usable and location.value is not None:
            return location.value.province
        return None
    return item.province


def _provider_identity(item: EconomicEvidenceRecord) -> str | None:
    if item.dimensions is not None:
        provider = item.dimensions.provider_identity
        if provider.is_usable and provider.value is not None:
            return provider.value.provider_id
        return None
    return item.provider.strip() or None


def _geography_scope(item: EconomicEvidenceRecord) -> str | None:
    if isinstance(item.dimensions, EconomicEvidenceDimensionsV2):
        return _dimension_value(item, "geographic_reach")
    return _dimension_value(item, "market_scope")


def _conflicted_dimensions(item: EconomicEvidenceRecord | None) -> tuple[str, ...]:
    if item is None or item.dimensions is None:
        return ()
    return tuple(
        name
        for name, value in item.dimensions.all_dimensions().items()
        if value.status in {DimensionStatus.CONFLICTED, DimensionStatus.AMBIGUOUS}
    )


def _unique(reasons: list[EvidenceExclusionReason]) -> tuple[EvidenceExclusionReason, ...]:
    present = set(reasons)
    return tuple(reason for reason in EvidenceExclusionReason if reason in present)


def _economic_object_kind(role: SemanticObservationRole) -> EconomicObjectKind:
    if role is SemanticObservationRole.SINGLE_SERVICE:
        return EconomicObjectKind.SERVICE
    if role is SemanticObservationRole.COMPOSITE_SERVICE:
        return EconomicObjectKind.COMPOSITE_SERVICE
    if role is SemanticObservationRole.HARDWARE_PRODUCT:
        return EconomicObjectKind.HARDWARE
    if role in {SemanticObservationRole.PRICE_CONTEXT, SemanticObservationRole.SCOPE_DEVICE, SemanticObservationRole.LOGISTICS_CONTEXT}:
        return EconomicObjectKind.CONTEXT
    if role is SemanticObservationRole.NON_OBJECT:
        return EconomicObjectKind.NON_ECONOMIC
    return EconomicObjectKind.UNKNOWN
