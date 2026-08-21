from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata


class SemanticResolutionStatus(Enum):
    RESOLVED = "RESOLVED"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class SemanticContext(Enum):
    USER_QUERY = "USER_QUERY"
    PROVIDER_OBSERVATION = "PROVIDER_OBSERVATION"
    TECHNICAL_NEED = "TECHNICAL_NEED"


@dataclass(frozen=True)
class KnowledgeProvenance:
    origin_type: str
    origin_reference: str
    origin_version: str | None = None

    def __post_init__(self) -> None:
        if not self.origin_type or not self.origin_type.strip():
            raise ValueError("KnowledgeProvenance requires origin_type.")
        if not self.origin_reference or not self.origin_reference.strip():
            raise ValueError("KnowledgeProvenance requires origin_reference.")


@dataclass(frozen=True)
class SemanticConcept:
    concept_id: str
    concept_type: str
    canonical_name: str | None = None
    ontology_version: str = "v1"

    def __post_init__(self) -> None:
        if not self.concept_id or not self.concept_id.strip():
            raise ValueError("SemanticConcept requires concept_id.")
        if not self.concept_type or not self.concept_type.strip():
            raise ValueError("SemanticConcept requires concept_type.")


@dataclass(frozen=True)
class SemanticAlias:
    expression: str
    concept_id: str
    context: SemanticContext
    provenance: KnowledgeProvenance

    def __post_init__(self) -> None:
        if not self.expression or not self.expression.strip():
            raise ValueError("SemanticAlias requires expression.")
        if not self.concept_id or not self.concept_id.strip():
            raise ValueError("SemanticAlias requires concept_id.")
        if self.provenance is None:
            raise ValueError("SemanticAlias requires provenance.")


@dataclass(frozen=True)
class SemanticCandidate:
    concept: SemanticConcept
    alias: SemanticAlias
    provenance: KnowledgeProvenance


@dataclass(frozen=True)
class SemanticResolution:
    expression: str
    context: SemanticContext
    status: SemanticResolutionStatus
    candidates: tuple[SemanticCandidate, ...] = ()


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())


class SemanticKnowledgeIndex:
    def __init__(
        self,
        *,
        concepts: tuple[SemanticConcept, ...],
        aliases: tuple[SemanticAlias, ...],
    ) -> None:
        self._concepts = {concept.concept_id: concept for concept in concepts}
        self._aliases = aliases

        missing = tuple(
            alias.concept_id
            for alias in aliases
            if alias.concept_id not in self._concepts
        )
        if missing:
            raise ValueError(
                "SemanticAlias references unknown concept_id: "
                + ", ".join(sorted(set(missing)))
            )

    def resolve(
        self,
        expression: str,
        *,
        context: SemanticContext,
    ) -> SemanticResolution:
        folded_expression = _fold(expression)
        candidates = tuple(
            SemanticCandidate(
                concept=self._concepts[alias.concept_id],
                alias=alias,
                provenance=alias.provenance,
            )
            for alias in self._aliases
            if alias.context is context and _fold(alias.expression) == folded_expression
        )

        if not candidates:
            return SemanticResolution(
                expression=expression,
                context=context,
                status=SemanticResolutionStatus.UNKNOWN,
            )

        concept_ids = {candidate.concept.concept_id for candidate in candidates}
        status = (
            SemanticResolutionStatus.RESOLVED
            if len(concept_ids) == 1
            else SemanticResolutionStatus.AMBIGUOUS
        )
        return SemanticResolution(
            expression=expression,
            context=context,
            status=status,
            candidates=candidates,
        )
