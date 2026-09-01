from __future__ import annotations

import hashlib

from src.aplicacion.language_query_contract import (
    EconomicObjectKind,
    MarketScope,
    ParsedPricingQuery,
)
from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
)
from src.dominio.user_query_understanding import (
    UserQueryFactOrigin,
    UserQueryMonetaryComponentOrigin,
    UserQueryMonetaryComponentRole,
    UserQuerySemanticFact,
    UserQuerySemanticRelation,
    UserQueryUnderstandingEnvelope,
    UserQueryUnderstandingStatus,
)


PROJECTOR_VERSION = "user-query-understanding-v2"
PARSER_VERSION = "pricing-query-parser-v1"


def project_user_query_understanding(
    parsed: ParsedPricingQuery,
) -> UserQueryUnderstandingEnvelope:
    reference = _query_reference(
        parsed.raw_text,
    )

    raw_provenance = KnowledgeProvenance(
        origin_type=parsed.language_evidence_type or "UNKNOWN",
        origin_reference=reference,
    )

    interpretation_provenance = KnowledgeProvenance(
        origin_type="PRICING_QUERY_PARSER",
        origin_reference=reference,
        origin_version=PARSER_VERSION,
    )

    projection_provenance = KnowledgeProvenance(
        origin_type="USER_QUERY_UNDERSTANDING_PROJECTOR",
        origin_reference=reference,
        origin_version=PROJECTOR_VERSION,
    )

    facts = _facts(
        parsed,
        interpretation_provenance,
    )

    relations = _relations(
        parsed,
        interpretation_provenance,
    )

    unknowns = _unknowns(
        parsed,
    )

    clarification_reasons = _clarification_reasons(
        parsed,
    )

    status = _status(
        parsed,
        unknowns=unknowns,
        clarification_reasons=clarification_reasons,
    )

    return UserQueryUnderstandingEnvelope(
        raw_text=parsed.raw_text,
        status=status,
        facts=facts,
        relations=relations,
        unknowns=unknowns,
        clarification_reasons=clarification_reasons,
        raw_provenance=raw_provenance,
        interpretation_provenance=interpretation_provenance,
        projection_provenance=projection_provenance,
    )


def _query_reference(raw_text: str) -> str:
    digest = hashlib.sha256(
        raw_text.encode("utf-8")
    ).hexdigest()[:24]

    return f"user-query:{digest}"


def _origin(
    parsed: ParsedPricingQuery,
    field: str,
) -> UserQueryFactOrigin:
    metadata = parsed.metadata

    if field in metadata.explicit_fields:
        return UserQueryFactOrigin.EXPLICIT

    if field in metadata.inferred_fields:
        return UserQueryFactOrigin.INFERRED

    if field in metadata.derived_fields:
        return UserQueryFactOrigin.DERIVED

    return UserQueryFactOrigin.PARSER_CLASSIFICATION


def _fact(
    parsed: ParsedPricingQuery,
    provenance: KnowledgeProvenance,
    field: str,
    value: object,
) -> UserQuerySemanticFact:
    return UserQuerySemanticFact(
        field=field,
        value=value,
        origin=_origin(
            parsed,
            field,
        ),
        provenance=provenance,
    )


def _facts(
    parsed: ParsedPricingQuery,
    provenance: KnowledgeProvenance,
) -> tuple[UserQuerySemanticFact, ...]:
    facts: list[UserQuerySemanticFact] = []

    if parsed.query_kind.value != "UNKNOWN":
        facts.append(
            _fact(
                parsed,
                provenance,
                "query_kind",
                parsed.query_kind.value,
            )
        )

    if parsed.intent_action.value != "UNKNOWN":
        facts.append(
            _fact(
                parsed,
                provenance,
                "intent_action",
                parsed.intent_action.value,
            )
        )

    if parsed.intent_side.value != "UNKNOWN":
        facts.append(
            _fact(
                parsed,
                provenance,
                "intent_side",
                parsed.intent_side.value,
            )
        )

    if parsed.economic_object_kind.value != "UNKNOWN":
        facts.append(
            _fact(
                parsed,
                provenance,
                "economic_object_kind",
                parsed.economic_object_kind.value,
            )
        )

    if parsed.canonical_services:
        facts.append(
            _fact(
                parsed,
                provenance,
                "canonical_services",
                tuple(parsed.canonical_services),
            )
        )

    if parsed.market_scope is not MarketScope.UNKNOWN:
        facts.append(
            _fact(
                parsed,
                provenance,
                "market_scope",
                parsed.market_scope.value,
            )
        )

    if parsed.modality.value != "UNKNOWN":
        facts.append(
            _fact(
                parsed,
                provenance,
                "modality",
                parsed.modality.value,
            )
        )

    if parsed.geography.raw_location:
        facts.append(
            _fact(
                parsed,
                provenance,
                "geography.raw_location",
                parsed.geography.raw_location,
            )
        )

    if parsed.geography.province:
        facts.append(
            _fact(
                parsed,
                provenance,
                "geography.province",
                parsed.geography.province,
            )
        )

    if parsed.geography.city:
        facts.append(
            _fact(
                parsed,
                provenance,
                "geography.city",
                parsed.geography.city,
            )
        )

    if parsed.device_type:
        facts.append(
            _fact(
                parsed,
                provenance,
                "device_type",
                parsed.device_type,
            )
        )

    if parsed.condition != "UNKNOWN":
        facts.append(
            _fact(
                parsed,
                provenance,
                "condition",
                parsed.condition,
            )
        )

    if parsed.price.value is not None:
        facts.append(
            _fact(
                parsed,
                provenance,
                "price.value",
                parsed.price.value,
            )
        )

    if (
        parsed.price.min is not None
        or parsed.price.max is not None
    ):
        facts.append(
            _fact(
                parsed,
                provenance,
                "price.range",
                (
                    parsed.price.min,
                    parsed.price.max,
                ),
            )
        )

    if parsed.price.currency != "UNKNOWN":
        facts.append(
            _fact(
                parsed,
                provenance,
                "price.currency",
                parsed.price.currency,
            )
        )

    if (
        parsed.price_scope.comparison_scope
        != "UNKNOWN"
    ):
        facts.append(
            _fact(
                parsed,
                provenance,
                "price_scope",
                parsed.price_scope.comparison_scope,
            )
        )

    for component in parsed.monetary_components:
        origin = (
            UserQueryFactOrigin.EXPLICIT
            if component.origin
            is UserQueryMonetaryComponentOrigin.EXPLICIT
            else UserQueryFactOrigin.DERIVED
        )

        facts.append(
            UserQuerySemanticFact(
                field=(
                    "monetary_component."
                    + component.role.value.lower()
                ),
                value={
                    "role": component.role.value,
                    "amount": component.value,
                    "currency": component.currency,
                    "raw_expression": (
                        component.raw_expression
                    ),
                    "derivation_method": (
                        component.derivation_method
                    ),
                    "derived_from": tuple(
                        item.value
                        for item in component.derived_from
                    ),
                },
                origin=origin,
                provenance=provenance,
            )
        )

    return tuple(facts)


def _relations(
    parsed: ParsedPricingQuery,
    provenance: KnowledgeProvenance,
) -> tuple[UserQuerySemanticRelation, ...]:
    relations: list[UserQuerySemanticRelation] = []

    for service in parsed.canonical_services:
        relations.append(
            UserQuerySemanticRelation(
                subject="QUERY",
                predicate="HAS_SERVICE",
                object=service,
                provenance=provenance,
            )
        )

    if parsed.market_scope is not MarketScope.UNKNOWN:
        relations.append(
            UserQuerySemanticRelation(
                subject="QUERY",
                predicate="HAS_MARKET_SCOPE",
                object=parsed.market_scope.value,
                provenance=provenance,
            )
        )

    if parsed.modality.value != "UNKNOWN":
        relations.append(
            UserQuerySemanticRelation(
                subject="QUERY",
                predicate="HAS_MODALITY",
                object=parsed.modality.value,
                provenance=provenance,
            )
        )

    if parsed.geography.province:
        relations.append(
            UserQuerySemanticRelation(
                subject="QUERY",
                predicate="LOCATED_IN",
                object=parsed.geography.province,
                provenance=provenance,
            )
        )

    if parsed.device_type:
        relations.append(
            UserQuerySemanticRelation(
                subject="QUERY",
                predicate="HAS_DEVICE",
                object=parsed.device_type,
                provenance=provenance,
            )
        )

    if (
        parsed.price_scope.comparison_scope
        != "UNKNOWN"
    ):
        relations.append(
            UserQuerySemanticRelation(
                subject="QUERY",
                predicate="HAS_PRICE_SCOPE",
                object=parsed.price_scope.comparison_scope,
                provenance=provenance,
            )
        )

    monetary_roles = {
        item.role
        for item in parsed.monetary_components
    }

    if (
        UserQueryMonetaryComponentRole.TOTAL_CHARGED
        in monetary_roles
    ):
        for component_role in (
            UserQueryMonetaryComponentRole.MATERIAL_COST,
            UserQueryMonetaryComponentRole.LABOR,
        ):
            if component_role not in monetary_roles:
                continue

            relations.append(
                UserQuerySemanticRelation(
                    subject="TOTAL_CHARGED",
                    predicate="INCLUDES_COMPONENT",
                    object=component_role.value,
                    provenance=provenance,
                )
            )

    return tuple(relations)


def _unknowns(
    parsed: ParsedPricingQuery,
) -> tuple[str, ...]:
    unknowns: set[str] = set()

    if parsed.intent_action.value == "UNKNOWN":
        unknowns.add(
            "intent_action"
        )

    if parsed.intent_side.value == "UNKNOWN":
        unknowns.add(
            "intent_side"
        )

    if (
        parsed.economic_object_kind
        is EconomicObjectKind.UNKNOWN
    ):
        unknowns.add(
            "economic_object_kind"
        )

    if parsed.market_scope is MarketScope.UNKNOWN:
        unknowns.add(
            "market_scope"
        )

    if (
        parsed.market_scope is MarketScope.LOCAL
        and parsed.geography.province is None
    ):
        unknowns.add(
            "geography.province"
        )

    has_price = (
        parsed.price.value is not None
        or parsed.price.min is not None
        or parsed.price.max is not None
    )

    if (
        has_price
        and parsed.price.currency == "UNKNOWN"
    ):
        unknowns.add(
            "price.currency"
        )

    return tuple(sorted(unknowns))


def _clarification_reasons(
    parsed: ParsedPricingQuery,
) -> tuple[str, ...]:
    raw = (
        parsed.metadata.clarification_reason
        or ""
    )

    return tuple(
        dict.fromkeys(
            item
            for item in raw.split("|")
            if item
        )
    )


def _status(
    parsed: ParsedPricingQuery,
    *,
    unknowns: tuple[str, ...],
    clarification_reasons: tuple[str, ...],
) -> UserQueryUnderstandingStatus:
    ambiguity_reasons = {
        "MULTIPLE_MONETARY_MENTIONS",
        "BUNDLE_REQUIRES_COMPARABLE_SCOPE",
    }

    if (
        ambiguity_reasons
        & set(clarification_reasons)
    ):
        return UserQueryUnderstandingStatus.AMBIGUOUS

    if (
        parsed.economic_object_kind
        is EconomicObjectKind.UNKNOWN
    ):
        return UserQueryUnderstandingStatus.UNKNOWN

    if (
        unknowns
        or parsed.metadata.clarification_required
    ):
        return UserQueryUnderstandingStatus.PARTIAL

    return UserQueryUnderstandingStatus.REPRESENTED
