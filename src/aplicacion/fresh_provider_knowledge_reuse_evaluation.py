from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata

from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
    SemanticContext,
    SemanticKnowledgeIndex,
    SemanticResolutionStatus,
)


class FreshKnowledgeReuseClass(Enum):
    EXACT_MEMORY_REUSE = "EXACT_MEMORY_REUSE"
    FRESH_UNSEEN_CANONICAL_CORE_UNKNOWN = "FRESH_UNSEEN_CANONICAL_CORE_UNKNOWN"
    LIVE_GENERALIZATION = "LIVE_GENERALIZATION"
    SEED_SEEN_NON_ALIAS_CORE_UNKNOWN = "SEED_SEEN_NON_ALIAS_CORE_UNKNOWN"
    SHARED_PARITY_ON_FRESH = "SHARED_PARITY_ON_FRESH"
    CORE_MEMORY_LEGACY_UNKNOWN = "CORE_MEMORY_LEGACY_UNKNOWN"
    SEMANTIC_DISAGREEMENT = "SEMANTIC_DISAGREEMENT"
    CORE_AMBIGUOUS = "CORE_AMBIGUOUS"
    BOTH_UNKNOWN = "BOTH_UNKNOWN"
    NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True)
class FreshProviderKnowledgeReuseResult:
    observation_id: str
    expression: str
    source: str
    provider: str
    province: str
    legacy_semantic_role: str
    legacy_canonical_service: str
    expression_seen_in_seed: bool
    expression_seen_in_seed_corpus: bool
    reuse_class: FreshKnowledgeReuseClass
    core_status: SemanticResolutionStatus
    core_candidate_concepts: tuple[str, ...]
    core_provenance: tuple[KnowledgeProvenance, ...]


class FreshProviderKnowledgeReuseEvaluator:
    def __init__(
        self,
        core_index: SemanticKnowledgeIndex,
        *,
        seed_expressions: set[str],
        seed_corpus_expressions: set[str] | None = None,
        legacy_interpreter: str = "UNKNOWN",
    ) -> None:
        self._core_index = core_index
        self._seed_expression_folds = {_fold(expression) for expression in seed_expressions}
        corpus_expressions = seed_corpus_expressions or seed_expressions
        self._seed_corpus_expression_folds = {
            _fold(expression) for expression in corpus_expressions
        }
        self._legacy_interpreter = legacy_interpreter

    def evaluate_row(self, row: dict[str, str]) -> FreshProviderKnowledgeReuseResult:
        expression = _clean(row.get("economic_object_raw"))
        legacy_role = _clean(row.get("semantic_role"))
        legacy_canonical = _clean(row.get("canonical_service"))
        core = self._core_index.resolve(
            expression,
            context=SemanticContext.PROVIDER_OBSERVATION,
        )
        core_candidates = tuple(candidate.concept.concept_id for candidate in core.candidates)
        core_provenance = tuple(candidate.provenance for candidate in core.candidates)
        expression_seen = _fold(expression) in self._seed_expression_folds
        expression_seen_in_seed_corpus = (
            _fold(expression) in self._seed_corpus_expression_folds
        )

        return FreshProviderKnowledgeReuseResult(
            observation_id=_clean(row.get("observation_id")),
            expression=expression,
            source=_clean(row.get("source")),
            provider=_clean(row.get("provider")) or _clean(row.get("source")),
            province=_clean(row.get("province")),
            legacy_semantic_role=legacy_role,
            legacy_canonical_service=legacy_canonical,
            expression_seen_in_seed=expression_seen,
            expression_seen_in_seed_corpus=expression_seen_in_seed_corpus,
            reuse_class=_classify(
                legacy_role=legacy_role,
                legacy_canonical=legacy_canonical,
                core_status=core.status,
                core_candidates=core_candidates,
                expression_seen=expression_seen,
                expression_seen_in_seed_corpus=expression_seen_in_seed_corpus,
                legacy_interpreter=self._legacy_interpreter,
            ),
            core_status=core.status,
            core_candidate_concepts=core_candidates,
            core_provenance=core_provenance,
        )


def _classify(
    *,
    legacy_role: str,
    legacy_canonical: str,
    core_status: SemanticResolutionStatus,
    core_candidates: tuple[str, ...],
    expression_seen: bool,
    expression_seen_in_seed_corpus: bool,
    legacy_interpreter: str,
) -> FreshKnowledgeReuseClass:
    if legacy_role not in {"SINGLE_SERVICE", "UNMAPPED"} and not legacy_canonical:
        return FreshKnowledgeReuseClass.NOT_COMPARABLE

    if core_status is SemanticResolutionStatus.AMBIGUOUS:
        return FreshKnowledgeReuseClass.CORE_AMBIGUOUS

    unique_core_concepts = set(core_candidates)

    if legacy_canonical and core_status is SemanticResolutionStatus.UNKNOWN:
        if expression_seen_in_seed_corpus and not expression_seen:
            return FreshKnowledgeReuseClass.SEED_SEEN_NON_ALIAS_CORE_UNKNOWN
        if legacy_interpreter == "semantic_normalization_live":
            return FreshKnowledgeReuseClass.LIVE_GENERALIZATION
        return FreshKnowledgeReuseClass.FRESH_UNSEEN_CANONICAL_CORE_UNKNOWN

    if not legacy_canonical and core_status is SemanticResolutionStatus.RESOLVED:
        return FreshKnowledgeReuseClass.CORE_MEMORY_LEGACY_UNKNOWN

    if legacy_canonical and core_status is SemanticResolutionStatus.RESOLVED:
        if unique_core_concepts == {legacy_canonical}:
            if expression_seen:
                return FreshKnowledgeReuseClass.EXACT_MEMORY_REUSE
            return FreshKnowledgeReuseClass.SHARED_PARITY_ON_FRESH
        return FreshKnowledgeReuseClass.SEMANTIC_DISAGREEMENT

    return FreshKnowledgeReuseClass.BOTH_UNKNOWN


def _clean(value: object) -> str:
    return str(value or "").strip()


def _fold(text: object) -> str:
    normalized = unicodedata.normalize("NFKD", _clean(text))
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())
