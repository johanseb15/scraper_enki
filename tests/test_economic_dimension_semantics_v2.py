from src.dominio.economic_evidence import (
    DimensionCardinality,
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    dimension_definition,
    resolve_scalar_dimension,
    resolve_set_dimension,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance


def claim(value, origin=DimensionOrigin.RAW_SOURCE_OBSERVATION):
    return DimensionClaim(
        value,
        origin,
        KnowledgeProvenance("TEST", f"claim:{value}", "v2"),
        str(value),
    )


def test_dimension_cardinality_is_explicit_and_domain_specific():
    expected = {
        "provider_identity": DimensionCardinality.SCALAR,
        "price_scope": DimensionCardinality.SCALAR,
        "currency": DimensionCardinality.SCALAR,
        "delivery_mode": DimensionCardinality.SCALAR,
        "geographic_reach": DimensionCardinality.HIERARCHICAL,
        "location": DimensionCardinality.STRUCTURED,
        "commercial_context": DimensionCardinality.MULTI_VALUE_SET,
        "bundle_status": DimensionCardinality.SCALAR,
        "hardware_included": DimensionCardinality.BOOLEAN,
        "materials_included": DimensionCardinality.BOOLEAN,
        "device_scope": DimensionCardinality.MULTI_VALUE_SET,
    }
    assert {
        name: dimension_definition(name).cardinality for name in expected
    } == expected


def test_compatible_set_claims_are_resolved_not_ambiguous():
    dimension = resolve_set_dimension(
        claim("URGENCY"),
        claim("AFTER_HOURS"),
    )
    assert dimension.status is DimensionStatus.OBSERVED
    assert dimension.value == frozenset({"URGENCY", "AFTER_HOURS"})
    assert [item.value for item in dimension.claims] == ["URGENCY", "AFTER_HOURS"]


def test_scalar_disagreement_between_raw_and_normalized_is_a_true_conflict():
    dimension = resolve_scalar_dimension(
        claim("USD"),
        claim("ARS", DimensionOrigin.NORMALIZED_FIELD),
    )
    assert dimension.status is DimensionStatus.CONFLICTED
    assert dimension.value is None


def test_same_source_scalar_alternatives_remain_real_ambiguity():
    dimension = resolve_scalar_dimension(claim("REMOTE"), claim("ONSITE"))
    assert dimension.status is DimensionStatus.AMBIGUOUS


def test_incompatible_set_claims_remain_ambiguous_when_semantics_say_so():
    dimension = resolve_set_dimension(
        claim("STANDARD"),
        claim("URGENCY"),
        incompatible_pairs=(("STANDARD", "URGENCY"),),
    )
    assert dimension.status is DimensionStatus.AMBIGUOUS
    assert dimension.value is None
