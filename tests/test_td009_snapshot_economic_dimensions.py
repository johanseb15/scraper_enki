from __future__ import annotations

from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    DimensionValue,
    EconomicEvidenceDimensionsV2,
    LocationDimension,
    ProviderIdentity,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.infraestructura.offer_snapshot_dimensions import (
    compose_snapshot_economic_dimensions,
)


def _raw_claim(value, raw_document_id):
    return DimensionClaim(
        value=value,
        origin=DimensionOrigin.RAW_SOURCE_OBSERVATION,
        provenance=KnowledgeProvenance(
            "RAW_SOURCE_EXPRESSION",
            (
                f"raw_document_id={raw_document_id};"
                "provenance=test"
            ),
            "test-v1",
        ),
        raw_basis="raw basis",
    )


def _normalized_claim(value):
    return DimensionClaim(
        value=value,
        origin=DimensionOrigin.NORMALIZED_FIELD,
        provenance=KnowledgeProvenance(
            "SEMANTIC_NORMALIZATION_FIELD",
            "artifact=semantic_normalization_v4",
            "semantic-normalization-v4",
        ),
        raw_basis="normalized field",
    )


def _registry_claim(value):
    return DimensionClaim(
        value=value,
        origin=DimensionOrigin.REGISTRY_CLAIM,
        provenance=KnowledgeProvenance(
            "PROVIDER_SOURCE_REGISTRY",
            "source=test;provider=Example",
            "pricing-source-registry-v1",
        ),
        raw_basis="registry claim",
    )


def _derived_claim(value):
    return DimensionClaim(
        value=value,
        origin=DimensionOrigin.DERIVED_CLAIM,
        provenance=KnowledgeProvenance(
            "ECONOMIC_DIMENSION_DERIVATION",
            "source=test;schema=v2",
            "economic-evidence-dimensions-v2",
        ),
        raw_basis="derived claim",
    )


def _dimensions():
    provider = ProviderIdentity(
        provider_id="provider:example:123",
        provider_name="Example",
        source="example_source",
    )

    location = LocationDimension(
        country=None,
        province="Buenos Aires",
        city="Buenos Aires",
    )

    return EconomicEvidenceDimensionsV2(
        provider_identity=DimensionValue(
            value=provider,
            status=DimensionStatus.INFERRED,
            claims=(_registry_claim(provider),),
        ),
        price_scope=DimensionValue(
            value="PER_HOUR",
            status=DimensionStatus.OBSERVED,
            claims=(
                _raw_claim(
                    "PER_HOUR",
                    "sha256:historical",
                ),
                _normalized_claim("PER_HOUR"),
            ),
        ),
        currency=DimensionValue(
            value="ARS",
            status=DimensionStatus.INFERRED,
            claims=(_normalized_claim("ARS"),),
        ),
        delivery_mode=DimensionValue(
            value="ONSITE",
            status=DimensionStatus.OBSERVED,
            claims=(
                _raw_claim(
                    "ONSITE",
                    "sha256:historical",
                ),
            ),
        ),
        geographic_reach=DimensionValue(
            value=None,
            status=DimensionStatus.UNKNOWN,
            claims=(),
        ),
        location=DimensionValue(
            value=location,
            status=DimensionStatus.INFERRED,
            claims=(_normalized_claim(location),),
        ),
        commercial_context=DimensionValue(
            value=frozenset({
                "AFTER_HOURS",
                "URGENCY",
            }),
            status=DimensionStatus.OBSERVED,
            claims=(
                _raw_claim(
                    "AFTER_HOURS",
                    "sha256:historical",
                ),
                _raw_claim(
                    "URGENCY",
                    "sha256:historical",
                ),
            ),
        ),
        bundle_status=DimensionValue(
            value="SIMPLE",
            status=DimensionStatus.INFERRED,
            claims=(_derived_claim("SIMPLE"),),
        ),
        hardware_included=DimensionValue(
            value=None,
            status=DimensionStatus.UNKNOWN,
            claims=(),
        ),
        materials_included=DimensionValue(
            value=None,
            status=DimensionStatus.UNKNOWN,
            claims=(),
        ),
        device_scope=DimensionValue(
            value=frozenset({
                "NOTEBOOK",
                "PC",
            }),
            status=DimensionStatus.OBSERVED,
            claims=(
                _raw_claim(
                    "NOTEBOOK",
                    "sha256:historical",
                ),
                _raw_claim(
                    "PC",
                    "sha256:historical",
                ),
            ),
        ),
    )


def test_historical_snapshot_preserves_snapshot_local_dimensions():
    result = compose_snapshot_economic_dimensions(
        _dimensions(),
        raw_document_id="sha256:historical",
    )

    assert result.delivery_mode.status is DimensionStatus.OBSERVED
    assert result.delivery_mode.value == "ONSITE"

    assert result.commercial_context.status is DimensionStatus.OBSERVED
    assert result.commercial_context.value == frozenset({
        "AFTER_HOURS",
        "URGENCY",
    })

    assert result.device_scope.status is DimensionStatus.OBSERVED
    assert result.device_scope.value == frozenset({
        "NOTEBOOK",
        "PC",
    })


def test_reacquired_snapshot_drops_historical_raw_dimensions():
    result = compose_snapshot_economic_dimensions(
        _dimensions(),
        raw_document_id="sha256:reacquired",
    )

    assert result.delivery_mode.status is DimensionStatus.UNKNOWN
    assert result.delivery_mode.value is None

    assert result.commercial_context.status is DimensionStatus.UNKNOWN
    assert result.commercial_context.value is None

    assert result.device_scope.status is DimensionStatus.UNKNOWN
    assert result.device_scope.value is None


def test_reacquired_snapshot_preserves_non_raw_context():
    result = compose_snapshot_economic_dimensions(
        _dimensions(),
        raw_document_id="sha256:reacquired",
    )

    assert result.provider_identity.status is DimensionStatus.INFERRED
    assert (
        result.provider_identity.value.provider_id
        == "provider:example:123"
    )

    assert result.currency.status is DimensionStatus.INFERRED
    assert result.currency.value == "ARS"

    assert result.location.status is DimensionStatus.INFERRED
    assert result.location.value.province == "Buenos Aires"

    assert result.bundle_status.status is DimensionStatus.INFERRED
    assert result.bundle_status.value == "SIMPLE"


def test_mixed_price_scope_is_recomputed_after_raw_claim_filter():
    result = compose_snapshot_economic_dimensions(
        _dimensions(),
        raw_document_id="sha256:reacquired",
    )

    assert result.price_scope.status is DimensionStatus.INFERRED
    assert result.price_scope.value == "PER_HOUR"
    assert len(result.price_scope.claims) == 1
    assert (
        result.price_scope.claims[0].origin
        is DimensionOrigin.NORMALIZED_FIELD
    )


def test_unknown_dimensions_remain_unknown():
    result = compose_snapshot_economic_dimensions(
        _dimensions(),
        raw_document_id="sha256:reacquired",
    )

    assert result.geographic_reach.status is DimensionStatus.UNKNOWN
    assert result.hardware_included.status is DimensionStatus.UNKNOWN
    assert result.materials_included.status is DimensionStatus.UNKNOWN


def test_full_snapshot_composition_preserves_v2_dimension_shape():
    result = compose_snapshot_economic_dimensions(
        _dimensions(),
        raw_document_id="sha256:historical",
    )

    assert isinstance(result, EconomicEvidenceDimensionsV2)

    assert set(result.all_dimensions()) == {
        "provider_identity",
        "price_scope",
        "currency",
        "delivery_mode",
        "geographic_reach",
        "location",
        "commercial_context",
        "bundle_status",
        "hardware_included",
        "materials_included",
        "device_scope",
    }

def test_commercial_context_incompatibility_survives_snapshot_recomposition():
    source = _dimensions()

    conflicting = EconomicEvidenceDimensionsV2(
        provider_identity=source.provider_identity,
        price_scope=source.price_scope,
        currency=source.currency,
        delivery_mode=source.delivery_mode,
        geographic_reach=source.geographic_reach,
        location=source.location,
        commercial_context=DimensionValue(
            value=None,
            status=DimensionStatus.AMBIGUOUS,
            claims=(
                _raw_claim(
                    "STANDARD",
                    "sha256:historical",
                ),
                _raw_claim(
                    "URGENCY",
                    "sha256:historical",
                ),
            ),
        ),
        bundle_status=source.bundle_status,
        hardware_included=source.hardware_included,
        materials_included=source.materials_included,
        device_scope=source.device_scope,
    )

    result = compose_snapshot_economic_dimensions(
        conflicting,
        raw_document_id="sha256:historical",
    )

    assert (
        result.commercial_context.status
        is DimensionStatus.AMBIGUOUS
    )
    assert result.commercial_context.value is None
    assert len(result.commercial_context.claims) == 2
