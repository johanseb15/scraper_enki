from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
    SemanticContext,
)


class UserQueryUnderstandingStatus(str, Enum):
    REPRESENTED = "REPRESENTED"
    PARTIAL = "PARTIAL"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class UserQueryFactOrigin(str, Enum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    DERIVED = "DERIVED"
    PARSER_CLASSIFICATION = "PARSER_CLASSIFICATION"


class UserQueryMonetaryComponentRole(str, Enum):
    TOTAL_CHARGED = "TOTAL_CHARGED"
    MATERIAL_COST = "MATERIAL_COST"
    LABOR = "LABOR"


class UserQueryMonetaryComponentOrigin(str, Enum):
    EXPLICIT = "EXPLICIT"
    DERIVED = "DERIVED"


@dataclass(frozen=True)
class UserQueryMonetaryComponent:
    role: UserQueryMonetaryComponentRole
    value: float
    currency: str
    origin: UserQueryMonetaryComponentOrigin
    raw_expression: str | None = None
    derivation_method: str | None = None
    derived_from: tuple[
        UserQueryMonetaryComponentRole,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(
                "UserQueryMonetaryComponent requires non-negative value."
            )

        if (
            self.origin
            is UserQueryMonetaryComponentOrigin.EXPLICIT
            and not self.raw_expression
        ):
            raise ValueError(
                "Explicit monetary component requires raw_expression."
            )

        if (
            self.origin
            is UserQueryMonetaryComponentOrigin.DERIVED
            and (
                not self.derivation_method
                or not self.derived_from
            )
        ):
            raise ValueError(
                "Derived monetary component requires derivation lineage."
            )


@dataclass(frozen=True)
class UserQuerySemanticFact:
    field: str
    value: object
    origin: UserQueryFactOrigin
    provenance: KnowledgeProvenance

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError(
                "UserQuerySemanticFact requires field."
            )

        if self.provenance is None:
            raise ValueError(
                "UserQuerySemanticFact requires provenance."
            )


@dataclass(frozen=True)
class UserQuerySemanticRelation:
    subject: str
    predicate: str
    object: str
    provenance: KnowledgeProvenance

    def __post_init__(self) -> None:
        if not self.subject or not self.subject.strip():
            raise ValueError(
                "UserQuerySemanticRelation requires subject."
            )

        if not self.predicate or not self.predicate.strip():
            raise ValueError(
                "UserQuerySemanticRelation requires predicate."
            )

        if not self.object or not self.object.strip():
            raise ValueError(
                "UserQuerySemanticRelation requires object."
            )

        if self.provenance is None:
            raise ValueError(
                "UserQuerySemanticRelation requires provenance."
            )


@dataclass(frozen=True)
class UserQueryUnderstandingEnvelope:
    raw_text: str
    status: UserQueryUnderstandingStatus
    facts: tuple[UserQuerySemanticFact, ...]
    relations: tuple[UserQuerySemanticRelation, ...]
    unknowns: tuple[str, ...]
    clarification_reasons: tuple[str, ...]
    raw_provenance: KnowledgeProvenance
    interpretation_provenance: KnowledgeProvenance
    projection_provenance: KnowledgeProvenance
    context: SemanticContext = SemanticContext.USER_QUERY

    def __post_init__(self) -> None:
        if not self.raw_text or not self.raw_text.strip():
            raise ValueError(
                "UserQueryUnderstandingEnvelope requires raw_text."
            )

        if self.context is not SemanticContext.USER_QUERY:
            raise ValueError(
                "User query understanding requires USER_QUERY context."
            )

        if self.raw_provenance is None:
            raise ValueError(
                "User query understanding requires raw provenance."
            )

        if self.interpretation_provenance is None:
            raise ValueError(
                "User query understanding requires interpretation provenance."
            )

        if self.projection_provenance is None:
            raise ValueError(
                "User query understanding requires projection provenance."
            )
