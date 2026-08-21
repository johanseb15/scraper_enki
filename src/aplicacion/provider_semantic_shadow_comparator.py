from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.aplicacion.semantic_normalization_live import (
    SemanticClassification,
    classify_new_observation,
)
from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
    SemanticContext,
    SemanticKnowledgeIndex,
    SemanticResolutionStatus,
)


class ProviderSemanticComparisonStatus(Enum):
    PARITY = "PARITY"
    CORE_UNKNOWN = "CORE_UNKNOWN"
    LEGACY_UNKNOWN_CORE_RESOLVED = "LEGACY_UNKNOWN_CORE_RESOLVED"
    LEGACY_RESOLVED_CORE_DIFFERENT = "LEGACY_RESOLVED_CORE_DIFFERENT"
    CORE_AMBIGUOUS = "CORE_AMBIGUOUS"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True)
class ProviderSemanticShadowComparison:
    input_expression: str
    legacy_classification: SemanticClassification
    status: ProviderSemanticComparisonStatus
    legacy_canonical_service: str
    legacy_semantic_role: str
    core_status: SemanticResolutionStatus
    core_candidate_concepts: tuple[str, ...]
    core_provenance: tuple[KnowledgeProvenance, ...]


class ProviderSemanticShadowComparator:
    def __init__(self, core_index: SemanticKnowledgeIndex) -> None:
        self._core_index = core_index

    def compare(
        self,
        expression: str,
        *,
        province: str,
    ) -> ProviderSemanticShadowComparison:
        legacy = classify_new_observation(expression, province=province)
        core = self._core_index.resolve(
            expression,
            context=SemanticContext.PROVIDER_OBSERVATION,
        )
        core_candidates = tuple(
            candidate.concept.concept_id for candidate in core.candidates
        )
        core_provenance = tuple(candidate.provenance for candidate in core.candidates)

        return ProviderSemanticShadowComparison(
            input_expression=expression,
            legacy_classification=legacy,
            status=_compare_status(legacy, core.status, core_candidates),
            legacy_canonical_service=legacy.canonical_service,
            legacy_semantic_role=legacy.semantic_role,
            core_status=core.status,
            core_candidate_concepts=core_candidates,
            core_provenance=core_provenance,
        )

    def normalize_with_shadow(
        self,
        expression: str,
        *,
        province: str,
    ) -> SemanticClassification:
        comparison = self.compare(expression, province=province)
        return comparison.legacy_classification


def _compare_status(
    legacy: SemanticClassification,
    core_status: SemanticResolutionStatus,
    core_candidates: tuple[str, ...],
) -> ProviderSemanticComparisonStatus:
    if core_status is SemanticResolutionStatus.AMBIGUOUS:
        return ProviderSemanticComparisonStatus.CORE_AMBIGUOUS

    legacy_canonical = legacy.canonical_service
    if legacy.semantic_role not in {"SINGLE_SERVICE", "UNMAPPED"} and not legacy_canonical:
        return ProviderSemanticComparisonStatus.NOT_COMPARABLE

    if legacy_canonical and core_status is SemanticResolutionStatus.UNKNOWN:
        return ProviderSemanticComparisonStatus.CORE_UNKNOWN

    if not legacy_canonical and core_status is SemanticResolutionStatus.RESOLVED:
        return ProviderSemanticComparisonStatus.LEGACY_UNKNOWN_CORE_RESOLVED

    if legacy_canonical and core_status is SemanticResolutionStatus.RESOLVED:
        if set(core_candidates) == {legacy_canonical}:
            return ProviderSemanticComparisonStatus.PARITY
        return ProviderSemanticComparisonStatus.LEGACY_RESOLVED_CORE_DIFFERENT

    return ProviderSemanticComparisonStatus.NOT_COMPARABLE
