from decimal import Decimal

import pytest

from src.aplicacion.semantic_economic_evidence_bridge import (
    SemanticEconomicEvidenceBridge,
)
from src.dominio.economic_evidence import (
    EconomicEvidenceRecord,
    EconomicReadiness,
    EvidenceExclusionReason,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    HardwareMeaningKind,
    HardwareMeaning,
    ObservationUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.dominio.semantic_understanding import SemanticUnderstandingEnvelope


def _provenance(reference: str) -> KnowledgeProvenance:
    return KnowledgeProvenance("TEST", reference, "v1")


def _envelope(
    role=SemanticObservationRole.SINGLE_SERVICE,
    *,
    observation_id="target",
    canonical="SOPORTE_REMOTO",
    matched=(),
    province="Córdoba",
    market_scope="LOCAL_SERVICE",
    status=ObservationUnderstandingStatus.FULLY_REPRESENTED,
    meaning=None,
):
    observation = SemanticObservation(
        observation_id=observation_id,
        raw_expression="target expression",
        semantic_role=role,
        market_scope=market_scope,
        source="target_source",
        provider="target_provider",
        province=province,
        canonical_service=(canonical if role is SemanticObservationRole.SINGLE_SERVICE else None),
        matched_services=matched,
        observation_provenance=_provenance(f"observation:{observation_id}"),
        interpretation_provenance=_provenance(f"interpretation:{observation_id}"),
    )
    return SemanticUnderstandingEnvelope(observation, status, meaning)


def _record(
    evidence_id,
    *,
    canonical="SOPORTE_REMOTO",
    role=SemanticObservationRole.SINGLE_SERVICE,
    provider=None,
    province="Córdoba",
    market_scope="LOCAL_SERVICE",
    price_scope="PER_HOUR",
    currency="ARS",
    price="100",
    matched=(),
    status=ObservationUnderstandingStatus.FULLY_REPRESENTED,
    meaning=None,
):
    return EconomicEvidenceRecord(
        evidence_id=evidence_id,
        raw_expression=f"evidence {evidence_id}",
        semantic_role=role,
        understanding_status=status,
        market_scope=market_scope,
        provider=provider or evidence_id,
        province=province,
        canonical_service=canonical if role is SemanticObservationRole.SINGLE_SERVICE else None,
        matched_services=matched,
        currency=currency,
        price_value=Decimal(price),
        price_scope=price_scope,
        commercial_context="STANDARD",
        provenance=_provenance(f"evidence:{evidence_id}"),
        meaning=meaning,
    )


def _bridge(*records):
    anchor = _record("target", provider="target_provider")
    return SemanticEconomicEvidenceBridge((anchor, *records))


def test_single_service_keeps_comparable_and_excluded_evidence_with_reasons():
    records = [
        _record("same"),
        _record("cadence", price_scope="PER_MONTH"),
        _record("geography", province="Mendoza"),
        _record("other_service", canonical="BACKUP_DATOS"),
        _record("usd", currency="USD"),
    ]

    context = _bridge(*records).resolve(_envelope())

    assert [item.evidence_id for item in context.comparable_evidence] == ["same"]
    reasons = {item.evidence.evidence_id: item.reasons for item in context.excluded_evidence}
    assert reasons["cadence"] == (EvidenceExclusionReason.CADENCE_MISMATCH,)
    assert reasons["geography"] == (EvidenceExclusionReason.GEOGRAPHY_MISMATCH,)
    assert reasons["other_service"] == (EvidenceExclusionReason.CANONICAL_SERVICE_MISMATCH,)
    assert reasons["usd"] == (EvidenceExclusionReason.CURRENCY_MISMATCH,)
    assert context.readiness is EconomicReadiness.INSUFFICIENT


def test_single_service_without_external_evidence_is_explicitly_insufficient():
    context = _bridge().resolve(_envelope())
    assert context.comparable_evidence == ()
    assert context.readiness is EconomicReadiness.INSUFFICIENT
    assert "COMPARABLE_EVIDENCE" in context.missing_dimensions
    assert context.excluded_evidence[0].reasons == (
        EvidenceExclusionReason.SELF_OBSERVATION_NOT_INDEPENDENT,
    )


def test_five_comparable_rows_require_three_independent_providers_for_ready():
    repeated = [_record(f"row-{index}", provider="one_provider", price=str(100 + index)) for index in range(5)]
    context = _bridge(*repeated).resolve(_envelope())
    assert context.independent_provider_count == 1
    assert context.readiness is EconomicReadiness.INSUFFICIENT

    independent = [
        _record("a1", provider="a", price="100"),
        _record("a2", provider="a", price="110"),
        _record("b1", provider="b", price="120"),
        _record("b2", provider="b", price="130"),
        _record("c1", provider="c", price="140"),
    ]
    ready = _bridge(*independent).resolve(_envelope())
    assert ready.independent_provider_count == 3
    assert ready.readiness is EconomicReadiness.READY


@pytest.mark.parametrize(
    ("role", "reason", "expected"),
    [
        (SemanticObservationRole.PRICE_CONTEXT, EvidenceExclusionReason.PRICE_CONTEXT_ONLY, EconomicReadiness.INSUFFICIENT),
        (SemanticObservationRole.SCOPE_DEVICE, EvidenceExclusionReason.SCOPE_ONLY, EconomicReadiness.INSUFFICIENT),
        (SemanticObservationRole.NON_OBJECT, EvidenceExclusionReason.NON_ECONOMIC_OBJECT, EconomicReadiness.INSUFFICIENT),
        (SemanticObservationRole.LOGISTICS_CONTEXT, EvidenceExclusionReason.LOGISTICS_ONLY, EconomicReadiness.INSUFFICIENT),
        (SemanticObservationRole.UNMAPPED, EvidenceExclusionReason.UNKNOWN_SEMANTICS, EconomicReadiness.UNKNOWN),
    ],
)
def test_context_roles_never_become_services(role, reason, expected):
    target = _envelope(
        role,
        canonical=None,
        status=(ObservationUnderstandingStatus.UNKNOWN if role is SemanticObservationRole.UNMAPPED else ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD),
    )
    context = _bridge(_record("service")).resolve(target)
    assert context.comparable_evidence == ()
    assert context.readiness is expected
    assert reason in context.exclusion_reasons


def test_composite_service_is_not_silently_decomposed():
    target = _envelope(
        SemanticObservationRole.COMPOSITE_SERVICE,
        canonical=None,
        matched=("FORMATEO_INSTALACION_SO", "BACKUP_DATOS"),
        status=ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD,
    )
    context = _bridge(_record("component", canonical="BACKUP_DATOS")).resolve(target)
    assert context.comparable_evidence == ()
    assert EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE in context.exclusion_reasons


def _hardware_meaning(kind, families):
    return HardwareMeaning(
        source_expression="hardware",
        meaning_kind=kind,
        families=tuple(families),
        provenance=_provenance("hardware-meaning"),
    )


def test_hardware_single_family_does_not_cross_service_or_system_boundary():
    target_meaning = _hardware_meaning(HardwareMeaningKind.SINGLE_COMPONENT_FAMILY, ("GPU",))
    target = _envelope(
        SemanticObservationRole.HARDWARE_PRODUCT,
        canonical=None,
        market_scope="GOODS_MARKET",
        status=ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD,
        meaning=target_meaning,
    )
    same = _record(
        "gpu",
        role=SemanticObservationRole.HARDWARE_PRODUCT,
        canonical=None,
        market_scope="GOODS_MARKET",
        province=None,
        price_scope="PER_UNIT",
        meaning=_hardware_meaning(HardwareMeaningKind.SINGLE_COMPONENT_FAMILY, ("GPU",)),
        status=ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD,
    )
    system = _record(
        "system",
        role=SemanticObservationRole.HARDWARE_PRODUCT,
        canonical=None,
        market_scope="GOODS_MARKET",
        province=None,
        price_scope="PER_UNIT",
        meaning=_hardware_meaning(HardwareMeaningKind.MULTI_COMPONENT_SYSTEM, ("GPU", "CPU")),
        status=ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD,
    )
    service = _record("service")
    anchor = _record(
        "target",
        role=SemanticObservationRole.HARDWARE_PRODUCT,
        canonical=None,
        market_scope="GOODS_MARKET",
        province=None,
        price_scope="PER_UNIT",
        meaning=target_meaning,
        status=ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD,
    )
    context = SemanticEconomicEvidenceBridge((anchor, same, system, service)).resolve(target)
    assert [item.evidence_id for item in context.comparable_evidence] == ["gpu"]
    reasons = {item.evidence.evidence_id: item.reasons for item in context.excluded_evidence}
    assert EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE in reasons["system"]
    assert EvidenceExclusionReason.HARDWARE_SERVICE_BOUNDARY in reasons["service"]


def test_hardware_multi_component_and_service_like_conflict_are_not_ready():
    multi = _envelope(
        SemanticObservationRole.HARDWARE_PRODUCT,
        canonical=None,
        market_scope="GOODS_MARKET",
        status=ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD,
        meaning=_hardware_meaning(HardwareMeaningKind.MULTI_COMPONENT_SYSTEM, ("GPU", "CPU")),
    )
    conflict = _envelope(
        SemanticObservationRole.HARDWARE_PRODUCT,
        canonical=None,
        market_scope="GOODS_MARKET",
        status=ObservationUnderstandingStatus.AMBIGUOUS,
        meaning=_hardware_meaning(HardwareMeaningKind.SERVICE_LIKE_CONFLICT, ()),
    )
    multi_anchor = _record(
        "target", role=SemanticObservationRole.HARDWARE_PRODUCT, canonical=None,
        market_scope="GOODS_MARKET", province=None, price_scope="PER_UNIT",
        meaning=multi.meaning, status=ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD,
    )
    conflict_anchor = _record(
        "target", role=SemanticObservationRole.HARDWARE_PRODUCT, canonical=None,
        market_scope="GOODS_MARKET", province=None, price_scope="PER_UNIT",
        meaning=conflict.meaning, status=ObservationUnderstandingStatus.AMBIGUOUS,
    )
    evidence = _record("service")
    assert SemanticEconomicEvidenceBridge((multi_anchor, evidence)).resolve(multi).readiness is EconomicReadiness.INSUFFICIENT
    assert SemanticEconomicEvidenceBridge((conflict_anchor, evidence)).resolve(conflict).readiness is EconomicReadiness.AMBIGUOUS


def test_unknown_and_ambiguous_statuses_remain_visible():
    unknown = _envelope(status=ObservationUnderstandingStatus.UNKNOWN)
    ambiguous = _envelope(status=ObservationUnderstandingStatus.AMBIGUOUS)
    evidence = _record("evidence")
    assert _bridge(evidence).resolve(unknown).readiness is EconomicReadiness.UNKNOWN
    assert _bridge(evidence).resolve(ambiguous).readiness is EconomicReadiness.AMBIGUOUS
