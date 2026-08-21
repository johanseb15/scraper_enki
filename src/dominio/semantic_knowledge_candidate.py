from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata

from src.dominio.semantic_knowledge import KnowledgeProvenance, SemanticContext


class KnowledgeCandidateStatus(Enum):
    OBSERVED = "OBSERVED"


@dataclass(frozen=True)
class KnowledgeCandidateObservation:
    expression: str
    context: SemanticContext
    proposed_concept_id: str
    observation_id: str
    source: str
    provider: str
    province: str | None
    observation_provenance: KnowledgeProvenance
    interpretation_provenance: KnowledgeProvenance
    status: KnowledgeCandidateStatus = KnowledgeCandidateStatus.OBSERVED

    def __post_init__(self) -> None:
        if not self.expression or not self.expression.strip():
            raise ValueError("KnowledgeCandidateObservation requires expression.")
        if not self.proposed_concept_id or not self.proposed_concept_id.strip():
            raise ValueError("KnowledgeCandidateObservation requires proposed_concept_id.")
        if not self.observation_id or not self.observation_id.strip():
            raise ValueError("KnowledgeCandidateObservation requires observation_id.")
        if self.observation_provenance is None:
            raise ValueError("KnowledgeCandidateObservation requires observation_provenance.")
        if self.interpretation_provenance is None:
            raise ValueError(
                "KnowledgeCandidateObservation requires interpretation_provenance."
            )

    @property
    def normalized_expression(self) -> str:
        return _fold(self.expression)


@dataclass(frozen=True)
class KnowledgeCandidateAggregate:
    expression: str
    normalized_expression: str
    context: SemanticContext
    proposed_concept_id: str
    status: KnowledgeCandidateStatus
    observations: tuple[KnowledgeCandidateObservation, ...]

    @property
    def observations_n(self) -> int:
        return len(self.observations)

    @property
    def providers_n(self) -> int:
        return len({observation.provider for observation in self.observations})

    @property
    def provinces_n(self) -> int:
        return len(
            {
                observation.province
                for observation in self.observations
                if observation.province
            }
        )


def unknown_interpretation_provenance() -> KnowledgeProvenance:
    return KnowledgeProvenance(
        "UNKNOWN",
        "UNKNOWN_INTERPRETATION_PROVENANCE",
    )


def aggregate_knowledge_candidates(
    observations: tuple[KnowledgeCandidateObservation, ...],
) -> tuple[KnowledgeCandidateAggregate, ...]:
    grouped: dict[
        tuple[str, SemanticContext, str], list[KnowledgeCandidateObservation]
    ] = {}
    for observation in observations:
        key = (
            observation.normalized_expression,
            observation.context,
            observation.proposed_concept_id,
        )
        grouped.setdefault(key, []).append(observation)

    aggregates = []
    for (normalized_expression, context, proposed_concept_id), group in sorted(
        grouped.items(),
        key=lambda item: (item[0][0], item[0][1].value, item[0][2]),
    ):
        ordered = tuple(
            sorted(
                group,
                key=lambda observation: (
                    observation.provider,
                    observation.observation_id,
                    observation.source,
                    observation.expression,
                ),
            )
        )
        aggregates.append(
            KnowledgeCandidateAggregate(
                expression=ordered[0].expression,
                normalized_expression=normalized_expression,
                context=context,
                proposed_concept_id=proposed_concept_id,
                status=KnowledgeCandidateStatus.OBSERVED,
                observations=ordered,
            )
        )

    return tuple(aggregates)


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())
