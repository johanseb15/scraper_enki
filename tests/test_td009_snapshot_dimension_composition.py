from __future__ import annotations

from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    DimensionValue,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.infraestructura.offer_snapshot_dimensions import (
    compose_snapshot_dimension,
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


def test_snapshot_keeps_raw_claim_from_same_raw_document():
    source = DimensionValue(
        value="ONSITE",
        status=DimensionStatus.OBSERVED,
        claims=(
            _raw_claim(
                "ONSITE",
                "sha256:historical",
            ),
        ),
    )

    result = compose_snapshot_dimension(
        source,
        raw_document_id="sha256:historical",
    )

    assert result.status is DimensionStatus.OBSERVED
    assert result.value == "ONSITE"
    assert len(result.claims) == 1


def test_snapshot_drops_raw_claim_from_different_raw_document():
    source = DimensionValue(
        value="ONSITE",
        status=DimensionStatus.OBSERVED,
        claims=(
            _raw_claim(
                "ONSITE",
                "sha256:historical",
            ),
        ),
    )

    result = compose_snapshot_dimension(
        source,
        raw_document_id="sha256:reacquired",
    )

    assert result.status is DimensionStatus.UNKNOWN
    assert result.value is None
    assert result.claims == ()


def test_snapshot_preserves_normalized_claim_without_raw_rebinding():
    source = DimensionValue(
        value="ARS",
        status=DimensionStatus.INFERRED,
        claims=(
            _normalized_claim("ARS"),
        ),
    )

    result = compose_snapshot_dimension(
        source,
        raw_document_id="sha256:reacquired",
    )

    assert result.status is DimensionStatus.INFERRED
    assert result.value == "ARS"
    assert result.claims == source.claims


def test_mixed_dimension_keeps_only_snapshot_compatible_claims():
    source = DimensionValue(
        value="PER_HOUR",
        status=DimensionStatus.OBSERVED,
        claims=(
            _raw_claim(
                "PER_HOUR",
                "sha256:historical",
            ),
            _normalized_claim("PER_HOUR"),
        ),
    )

    result = compose_snapshot_dimension(
        source,
        raw_document_id="sha256:reacquired",
    )

    assert result.status is DimensionStatus.INFERRED
    assert result.value == "PER_HOUR"
    assert len(result.claims) == 1
    assert (
        result.claims[0].origin
        is DimensionOrigin.NORMALIZED_FIELD
    )


def test_unknown_dimension_remains_unknown():
    source = DimensionValue(
        value=None,
        status=DimensionStatus.UNKNOWN,
        claims=(),
    )

    result = compose_snapshot_dimension(
        source,
        raw_document_id="sha256:any",
    )

    assert result.status is DimensionStatus.UNKNOWN
    assert result.value is None
    assert result.claims == ()


def test_conflict_is_recomputed_after_incompatible_raw_claim_is_removed():
    source = DimensionValue(
        value=None,
        status=DimensionStatus.CONFLICTED,
        claims=(
            _raw_claim(
                "ONSITE",
                "sha256:historical",
            ),
            _normalized_claim("REMOTE"),
        ),
    )

    result = compose_snapshot_dimension(
        source,
        raw_document_id="sha256:reacquired",
    )

    assert result.status is DimensionStatus.INFERRED
    assert result.value == "REMOTE"
    assert len(result.claims) == 1
