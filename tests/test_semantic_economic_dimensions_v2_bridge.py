from dataclasses import replace
from decimal import Decimal
import json

from src.aplicacion.semantic_economic_evidence_bridge import SemanticEconomicEvidenceBridge
from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    EconomicEvidenceDimensionsV2,
    EconomicEvidenceRecord,
    EconomicReadiness,
    EvidenceExclusionReason,
    LocationDimension,
    ProviderIdentity,
    resolve_scalar_dimension,
    resolve_set_dimension,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    ObservationUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.dominio.semantic_understanding import SemanticUnderstandingEnvelope
from src.infraestructura.semantic_economic_shadow_artifact import (
    write_semantic_economic_shadow_jsonl,
)


def provenance(reference):
    return KnowledgeProvenance("TEST", reference, "v2")


def claim(value, origin=DimensionOrigin.RAW_SOURCE_OBSERVATION):
    return DimensionClaim(value, origin, provenance(str(value)), str(value))


def dimensions(
    provider_id,
    *,
    currency="ARS",
    price_scope="PER_HOUR",
    delivery_mode="REMOTE",
    geographic_reach="NATIONAL",
    location=None,
    commercial_context=("URGENCY", "AFTER_HOURS"),
    bundle="SIMPLE",
):
    return EconomicEvidenceDimensionsV2(
        provider_identity=resolve_scalar_dimension(
            claim(ProviderIdentity(provider_id, provider_id, provider_id))
        ),
        price_scope=resolve_scalar_dimension(claim(price_scope)) if price_scope else resolve_scalar_dimension(),
        currency=resolve_scalar_dimension(claim(currency)) if currency else resolve_scalar_dimension(),
        delivery_mode=resolve_scalar_dimension(claim(delivery_mode)) if delivery_mode else resolve_scalar_dimension(),
        geographic_reach=(
            resolve_scalar_dimension(claim(geographic_reach))
            if geographic_reach else resolve_scalar_dimension()
        ),
        location=(
            resolve_scalar_dimension(claim(location))
            if location else resolve_scalar_dimension()
        ),
        commercial_context=resolve_set_dimension(
            *(claim(value) for value in commercial_context)
        ),
        bundle_status=resolve_scalar_dimension(claim(bundle)),
    )


def record(evidence_id, dimensions_value, price="100"):
    return EconomicEvidenceRecord(
        evidence_id=evidence_id,
        raw_expression=f"Soporte remoto por hora {evidence_id}",
        semantic_role=SemanticObservationRole.SINGLE_SERVICE,
        understanding_status=ObservationUnderstandingStatus.FULLY_REPRESENTED,
        market_scope="REMOTE_NATIONAL_SERVICE",
        provider=evidence_id,
        province=None,
        canonical_service="SOPORTE_REMOTO",
        matched_services=("SOPORTE_REMOTO",),
        currency="ARS",
        price_value=Decimal(price),
        price_scope="PER_HOUR",
        commercial_context="STANDARD",
        provenance=provenance(evidence_id),
        dimensions=dimensions_value,
    )


def envelope():
    observation = SemanticObservation(
        observation_id="target",
        raw_expression="Soporte remoto por hora",
        semantic_role=SemanticObservationRole.SINGLE_SERVICE,
        market_scope="REMOTE_NATIONAL_SERVICE",
        source="target",
        provider="target",
        province=None,
        canonical_service="SOPORTE_REMOTO",
        matched_services=("SOPORTE_REMOTO",),
        observation_provenance=provenance("target-observed"),
        interpretation_provenance=provenance("target-interpreted"),
    )
    return SemanticUnderstandingEnvelope(
        observation, ObservationUnderstandingStatus.FULLY_REPRESENTED, None
    )


def resolve(anchor_dimensions, candidate_dimensions):
    bridge = SemanticEconomicEvidenceBridge((
        record("target", anchor_dimensions),
        record("candidate", candidate_dimensions),
    ))
    return bridge.resolve(envelope())


def test_remote_national_compares_on_two_orthogonal_dimensions():
    context = resolve(dimensions("provider:a"), dimensions("provider:b"))
    assert [item.evidence_id for item in context.comparable_evidence] == ["candidate"]
    assert EvidenceExclusionReason.DIMENSION_CONFLICT not in context.exclusion_reasons


def test_remote_with_unknown_reach_is_conservatively_insufficient():
    context = resolve(
        dimensions("provider:a", geographic_reach=None),
        dimensions("provider:b", geographic_reach=None),
    )
    reasons = {item.evidence.evidence_id: item.reasons for item in context.excluded_evidence}
    assert EvidenceExclusionReason.INSUFFICIENT_SCOPE in reasons["candidate"]


def test_delivery_and_reach_mismatches_have_distinct_reasons():
    delivery = resolve(dimensions("provider:a"), dimensions("provider:b", delivery_mode="ONSITE"))
    reach = resolve(dimensions("provider:a"), dimensions("provider:b", geographic_reach="PROVINCE"))
    assert EvidenceExclusionReason.DELIVERY_MODE_MISMATCH in delivery.exclusion_reasons
    assert EvidenceExclusionReason.GEOGRAPHIC_REACH_MISMATCH in reach.exclusion_reasons


def test_commercial_context_uses_exact_set_semantics():
    exact = resolve(
        dimensions("provider:a", commercial_context=("URGENCY", "AFTER_HOURS")),
        dimensions("provider:b", commercial_context=("AFTER_HOURS", "URGENCY")),
    )
    subset = resolve(
        dimensions("provider:a", commercial_context=("URGENCY", "AFTER_HOURS")),
        dimensions("provider:b", commercial_context=("URGENCY",)),
    )
    assert [item.evidence_id for item in exact.comparable_evidence] == ["candidate"]
    assert EvidenceExclusionReason.COMMERCIAL_CONTEXT_MISMATCH in subset.exclusion_reasons


def test_true_currency_and_cadence_conflicts_remain_exclusions():
    currency = resolve(dimensions("provider:a"), dimensions("provider:b", currency="USD"))
    cadence = resolve(dimensions("provider:a"), dimensions("provider:b", price_scope="PER_MONTH"))
    assert EvidenceExclusionReason.CURRENCY_MISMATCH in currency.exclusion_reasons
    assert EvidenceExclusionReason.CADENCE_MISMATCH in cadence.exclusion_reasons


def test_real_scalar_ambiguity_is_not_treated_as_multivalue():
    ambiguous = dimensions("provider:a")
    ambiguous = EconomicEvidenceDimensionsV2(
        **{
            **ambiguous.__dict__,
            "delivery_mode": resolve_scalar_dimension(claim("REMOTE"), claim("ONSITE")),
        }
    )
    context = resolve(ambiguous, dimensions("provider:b"))
    assert context.readiness is EconomicReadiness.AMBIGUOUS
    assert "delivery_mode" in context.conflicted_dimensions
    assert EvidenceExclusionReason.DIMENSION_CONFLICT in context.exclusion_reasons


def test_location_is_required_for_onsite_but_not_used_as_remote_reach():
    cordoba = LocationDimension(province="Córdoba", city="Córdoba")
    mendoza = LocationDimension(province="Mendoza", city="Mendoza")
    onsite = resolve(
        dimensions("provider:a", delivery_mode="ONSITE", geographic_reach="PROVINCE", location=cordoba),
        dimensions("provider:b", delivery_mode="ONSITE", geographic_reach="PROVINCE", location=mendoza),
    )
    remote = resolve(
        dimensions("provider:a", location=cordoba),
        dimensions("provider:b", location=mendoza),
    )
    assert EvidenceExclusionReason.LOCATION_MISMATCH in onsite.exclusion_reasons
    assert [item.evidence_id for item in remote.comparable_evidence] == ["candidate"]


def test_provider_independence_uses_stable_identity_in_v2():
    anchor = record("target", dimensions("provider:a"))
    first = record("first", dimensions("provider:b"))
    second = replace(record("second", dimensions("provider:b")), price_value=Decimal("110"))
    context = SemanticEconomicEvidenceBridge((anchor, first, second)).resolve(envelope())
    assert context.evidence_count == 2
    assert context.independent_provider_count == 1


def test_v2_comparable_evidence_serializes_multivalue_deterministically(tmp_path):
    context = resolve(dimensions("provider:a"), dimensions("provider:b"))
    output = tmp_path / "shadow.jsonl"
    write_semantic_economic_shadow_jsonl((context,), output, version="test-v2")
    payload = json.loads(output.read_text(encoding="utf-8"))
    commercial = payload["comparable_evidence"][0]["dimensions"]["commercial_context"]
    assert commercial["value"] == ["AFTER_HOURS", "URGENCY"]
