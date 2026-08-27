from __future__ import annotations

from src.dominio.economic_evidence import (
    DimensionOrigin,
    DimensionStatus,
)
from src.infraestructura.economic_dimensions_v2_adapter import (
    derive_economic_dimensions_v2,
)


def _row():
    return {
        "observation_id": "70",
        "source": "example_source",
        "economic_object_raw": (
            "Visita a domicilio x 1 HS "
            "(Emergencia fuera de HS) PC-Notebook"
        ),
        "currency": "ARS",
        "semantic_role": "SINGLE_SERVICE",
        "province": "Buenos Aires",
        "city": "Buenos Aires",
    }


def _registry():
    return {
        "example_source": {
            "source": "example_source",
            "provider": "Example Provider",
        }
    }


def _raw_claims(dimension):
    return tuple(
        claim
        for claim in dimension.claims
        if claim.origin
        is DimensionOrigin.RAW_SOURCE_OBSERVATION
    )


def test_adapter_can_anchor_raw_expression_claims_to_specific_raw_document():
    dimensions = derive_economic_dimensions_v2(
        _row(),
        _registry(),
        raw_document_id="sha256:historical",
    )

    assert dimensions.delivery_mode.status is DimensionStatus.OBSERVED
    assert dimensions.commercial_context.status is DimensionStatus.OBSERVED
    assert dimensions.device_scope.status is DimensionStatus.OBSERVED

    raw_claims = (
        _raw_claims(dimensions.delivery_mode)
        + _raw_claims(dimensions.commercial_context)
        + _raw_claims(dimensions.device_scope)
    )

    assert raw_claims

    assert all(
        (
            "raw_document_id=sha256:historical"
            in claim.provenance.origin_reference
        )
        for claim in raw_claims
    )


def test_adapter_without_raw_document_id_keeps_legacy_provenance_shape():
    dimensions = derive_economic_dimensions_v2(
        _row(),
        _registry(),
    )

    raw_claims = (
        _raw_claims(dimensions.delivery_mode)
        + _raw_claims(dimensions.commercial_context)
        + _raw_claims(dimensions.device_scope)
    )

    assert raw_claims

    assert all(
        "raw_document_id=" not in claim.provenance.origin_reference
        for claim in raw_claims
    )


def test_raw_document_id_does_not_change_non_raw_dimension_semantics():
    legacy = derive_economic_dimensions_v2(
        _row(),
        _registry(),
    )

    anchored = derive_economic_dimensions_v2(
        _row(),
        _registry(),
        raw_document_id="sha256:historical",
    )

    assert (
        anchored.provider_identity.value
        == legacy.provider_identity.value
    )
    assert anchored.currency.value == legacy.currency.value
    assert anchored.location.value == legacy.location.value
    assert anchored.bundle_status.value == legacy.bundle_status.value
