from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    resolve_dimension,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance


def provenance(reference: str) -> KnowledgeProvenance:
    return KnowledgeProvenance("TEST", reference, "v1")


def test_observed_claim_wins_over_matching_inference_without_losing_provenance():
    observed = DimensionClaim("PER_HOUR", DimensionOrigin.OBSERVED, provenance("raw"), "por hora")
    inferred = DimensionClaim("PER_HOUR", DimensionOrigin.INFERRED, provenance("normalizer"), "rule:hour")

    dimension = resolve_dimension(observed, inferred)

    assert dimension.status is DimensionStatus.OBSERVED
    assert dimension.value == "PER_HOUR"
    assert dimension.claims == (observed, inferred)


def test_observed_and_inferred_disagreement_is_explicit_conflict():
    observed = DimensionClaim("PER_HOUR", DimensionOrigin.OBSERVED, provenance("raw"), "por hora")
    inferred = DimensionClaim("PER_MONTH", DimensionOrigin.INFERRED, provenance("normalizer"), "monthly")

    dimension = resolve_dimension(observed, inferred)

    assert dimension.status is DimensionStatus.CONFLICTED
    assert dimension.value is None
    assert dimension.claims == (observed, inferred)


def test_absent_claim_remains_unknown():
    dimension = resolve_dimension()

    assert dimension.status is DimensionStatus.UNKNOWN
    assert dimension.value is None
    assert dimension.claims == ()


def test_multiple_distinct_claims_from_same_origin_are_ambiguous_not_conflicted():
    dimension = resolve_dimension(
        DimensionClaim(
            "URGENCY",
            DimensionOrigin.OBSERVED,
            provenance("raw:urgency"),
            "urgencia",
        ),
        DimensionClaim(
            "AFTER_HOURS",
            DimensionOrigin.OBSERVED,
            provenance("raw:after-hours"),
            "fuera de horario",
        ),
    )

    assert dimension.status is DimensionStatus.AMBIGUOUS
    assert {item.value for item in dimension.claims} == {"URGENCY", "AFTER_HOURS"}
