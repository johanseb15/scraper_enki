from dataclasses import replace
from decimal import Decimal

from src.aplicacion.semantic_economic_evidence_bridge import SemanticEconomicEvidenceBridge
from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    EconomicEvidenceDimensions,
    EconomicEvidenceRecord,
    EconomicReadiness,
    EvidenceExclusionReason,
    GeographyDimension,
    ProviderIdentity,
    resolve_dimension,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    ObservationUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.dominio.semantic_understanding import SemanticUnderstandingEnvelope


def provenance(reference):
    return KnowledgeProvenance("TEST", reference, "v1")


def claim(value, origin=DimensionOrigin.OBSERVED, reference="dimension"):
    return DimensionClaim(value, origin, provenance(reference), str(value))


def dimensions(provider_id, *, currency="ARS", price_scope="PER_HOUR", bundle="SIMPLE"):
    return EconomicEvidenceDimensions(
        provider_identity=(
            resolve_dimension(claim(ProviderIdentity(provider_id, provider_id, provider_id)))
            if provider_id else resolve_dimension()
        ),
        price_scope=resolve_dimension(claim(price_scope)),
        geography=resolve_dimension(claim(GeographyDimension(province="Córdoba"))),
        market_scope=resolve_dimension(claim("LOCAL_SERVICE")),
        commercial_context=resolve_dimension(claim("STANDARD")),
        bundle_status=resolve_dimension(claim(bundle)),
        currency=resolve_dimension(claim(currency)),
    )


def record(evidence_id, provider, dimension_value, price="100"):
    return EconomicEvidenceRecord(
        evidence_id=evidence_id,
        raw_expression=f"Soporte por hora {evidence_id}",
        semantic_role=SemanticObservationRole.SINGLE_SERVICE,
        understanding_status=ObservationUnderstandingStatus.FULLY_REPRESENTED,
        market_scope="LOCAL_SERVICE",
        provider=provider,
        province="Córdoba",
        canonical_service="SOPORTE_REMOTO",
        matched_services=("SOPORTE_REMOTO",),
        currency="ARS",
        price_value=Decimal(price),
        price_scope="PER_HOUR",
        commercial_context="STANDARD",
        provenance=provenance(evidence_id),
        dimensions=dimension_value,
    )


def envelope():
    observation = SemanticObservation(
        observation_id="target",
        raw_expression="Soporte por hora",
        semantic_role=SemanticObservationRole.SINGLE_SERVICE,
        market_scope="LOCAL_SERVICE",
        source="page-a",
        provider="Provider A",
        province="Córdoba",
        canonical_service="SOPORTE_REMOTO",
        matched_services=("SOPORTE_REMOTO",),
        observation_provenance=provenance("target-observed"),
        interpretation_provenance=provenance("target-inferred"),
    )
    return SemanticUnderstandingEnvelope(
        observation,
        ObservationUnderstandingStatus.FULLY_REPRESENTED,
        None,
    )


def test_independence_counts_stable_provider_id_not_rows_or_source_names():
    records = [
        record("target", "page-a", dimensions("provider:a")),
        record("a-2", "page-b", dimensions("provider:a"), "110"),
        record("b-1", "page-c", dimensions("provider:b"), "120"),
        record("b-2", "page-d", dimensions("provider:b"), "130"),
        record("c-1", "page-e", dimensions("provider:c"), "140"),
        record("unknown", "unknown-page", dimensions(None), "150"),
    ]

    context = SemanticEconomicEvidenceBridge(records).resolve(envelope())

    assert context.independent_provider_count == 3
    assert context.readiness is EconomicReadiness.READY


def test_dimension_conflict_is_reported_and_reduces_readiness():
    conflicted_currency = EconomicEvidenceDimensions(
        provider_identity=resolve_dimension(claim(ProviderIdentity("provider:a", "A", "a"))),
        price_scope=resolve_dimension(claim("PER_HOUR")),
        market_scope=resolve_dimension(claim("LOCAL_SERVICE")),
        commercial_context=resolve_dimension(claim("STANDARD")),
        bundle_status=resolve_dimension(claim("SIMPLE")),
        currency=resolve_dimension(claim("USD"), claim("ARS", DimensionOrigin.INFERRED)),
    )
    records = [
        record("target", "a", conflicted_currency),
        record("other", "b", dimensions("provider:b")),
    ]

    context = SemanticEconomicEvidenceBridge(records).resolve(envelope())

    assert context.readiness is EconomicReadiness.AMBIGUOUS
    assert "currency" in context.conflicted_dimensions
    assert EvidenceExclusionReason.DIMENSION_CONFLICT in context.exclusion_reasons


def test_explicit_bundle_dimension_cannot_compare_with_simple_service():
    records = [
        record("target", "a", dimensions("provider:a")),
        record("bundle", "b", dimensions("provider:b", bundle="COMPOSITE")),
    ]

    context = SemanticEconomicEvidenceBridge(records).resolve(envelope())

    reasons = {item.evidence.evidence_id: item.reasons for item in context.excluded_evidence}
    assert EvidenceExclusionReason.BUNDLE_NOT_COMPARABLE in reasons["bundle"]


def test_role_index_reduces_pairs_without_changing_candidate_results():
    records = [
        record("target", "a", dimensions("provider:a")),
        record("one", "b", dimensions("provider:b")),
        record("two", "c", dimensions("provider:c")),
        replace(
            record("price-context", "d", dimensions("provider:d")),
            semantic_role=SemanticObservationRole.PRICE_CONTEXT,
            canonical_service=None,
        ),
        replace(
            record("scope", "e", dimensions("provider:e")),
            semantic_role=SemanticObservationRole.SCOPE_DEVICE,
            canonical_service=None,
        ),
    ]
    bridge = SemanticEconomicEvidenceBridge(records)

    context = bridge.resolve(envelope())
    metrics = bridge.candidate_generation_metrics

    assert [item.evidence_id for item in context.candidate_evidence] == ["target", "one", "two"]
    assert metrics["CANDIDATE_PAIRS_BEFORE_INDEX"] == 5
    assert metrics["CANDIDATE_PAIRS_AFTER_INDEX"] == 3
    assert metrics["CANDIDATE_RESULTS"] == 3
