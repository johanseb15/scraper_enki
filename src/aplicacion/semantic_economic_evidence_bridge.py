from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from src.dominio.economic_evidence import (
    EconomicEvidenceContext,
    EconomicEvidenceRecord,
    EconomicObjectKind,
    EconomicReadiness,
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

    def resolve(self, envelope: SemanticUnderstandingEnvelope) -> EconomicEvidenceContext:
        observation = envelope.observation
        anchor = next(
            (item for item in self._evidence if item.evidence_id == observation.observation_id),
            None,
        )
        candidates = tuple(
            item for item in self._evidence
            if self._is_candidate(
                observation.semantic_role,
                observation.observation_id,
                item,
            )
        )
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
        providers = len({item.provider for item in comparable if item.provider.strip()})
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
            geography_scope=(anchor.market_scope if anchor else observation.market_scope),
            price_scope=(anchor.price_scope if anchor else "UNKNOWN"),
            provenance=(observation.observation_provenance, observation.interpretation_provenance),
            uncertainty=uncertainty,
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
        if envelope.status is ObservationUnderstandingStatus.UNKNOWN:
            return (EvidenceExclusionReason.UNKNOWN_SEMANTICS,)
        if envelope.status is ObservationUnderstandingStatus.AMBIGUOUS:
            return (EvidenceExclusionReason.AMBIGUOUS_OBJECT,)
        if role in _CONTEXT_REASON:
            return (_CONTEXT_REASON[role],)
        if role is SemanticObservationRole.COMPOSITE_SERVICE:
            return (EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE,)
        if role is SemanticObservationRole.HARDWARE_PRODUCT:
            return self._hardware_reasons(envelope.meaning, anchor, item)
        return self._service_reasons(envelope, anchor, item)

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
            if anchor.price_scope == "UNKNOWN":
                missing.append("PRICE_SCOPE")
            if not anchor.currency or anchor.currency == "UNKNOWN":
                missing.append("CURRENCY")
            if anchor.market_scope == "LOCAL_SERVICE" and not anchor.province:
                missing.append("GEOGRAPHY")
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
        if any(name in missing for name in ("SOURCE_EVIDENCE_ROW", "PRICE_SCOPE", "CURRENCY", "GEOGRAPHY")):
            return EconomicReadiness.INSUFFICIENT
        prices = [item.price_value for item in comparable if item.price_value is not None and item.price_value > 0]
        providers = len({item.provider for item in comparable if item.provider.strip()})
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
    reasons: list[EvidenceExclusionReason] = []
    if anchor.market_scope != item.market_scope:
        reasons.append(EvidenceExclusionReason.MARKET_SCOPE_MISMATCH)
    elif require_geography and anchor.market_scope == "LOCAL_SERVICE":
        if not anchor.province or not item.province:
            reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
        elif anchor.province != item.province:
            reasons.append(EvidenceExclusionReason.GEOGRAPHY_MISMATCH)
    if not anchor.currency or anchor.currency == "UNKNOWN" or not item.currency or item.currency == "UNKNOWN":
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
    elif anchor.currency != item.currency:
        reasons.append(EvidenceExclusionReason.CURRENCY_MISMATCH)
    if anchor.price_scope == "UNKNOWN" or item.price_scope == "UNKNOWN":
        reasons.append(EvidenceExclusionReason.INSUFFICIENT_SCOPE)
    elif anchor.price_scope != item.price_scope:
        reasons.append(EvidenceExclusionReason.CADENCE_MISMATCH)
    if anchor.commercial_context != item.commercial_context:
        reasons.append(EvidenceExclusionReason.COMMERCIAL_CONTEXT_MISMATCH)
    if item.price_value is None or item.price_value <= 0:
        reasons.append(EvidenceExclusionReason.INVALID_PRICE)
    return reasons


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
