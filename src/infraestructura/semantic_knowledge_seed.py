from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
from pathlib import Path
import unicodedata

from src.dominio.semantic_knowledge import (
    KnowledgeProvenance,
    SemanticAlias,
    SemanticConcept,
    SemanticContext,
    SemanticKnowledgeIndex,
    SemanticResolutionStatus,
)


SEMANTIC_NORMALIZATION_V4_VERSION = "semantic_normalization_v4"
SEMANTIC_NORMALIZATION_V4_ORIGIN_TYPE = "SEMANTIC_NORMALIZATION_V4"
ELIGIBLE_ALIAS_SEMANTIC_ROLES = frozenset({"SINGLE_SERVICE"})


@dataclass(frozen=True)
class SemanticKnowledgeSeed:
    concepts: tuple[SemanticConcept, ...]
    aliases: tuple[SemanticAlias, ...]

    def concept_by_id(self, concept_id: str) -> SemanticConcept:
        for concept in self.concepts:
            if concept.concept_id == concept_id:
                return concept
        raise KeyError(concept_id)


@dataclass(frozen=True)
class SemanticRoleProfile:
    semantic_role: str
    rows: int
    with_canonical_service: int
    candidate_for_alias_seed: bool
    reason: str


@dataclass(frozen=True)
class SemanticNormalizationV4Profile:
    total_rows: int
    rows_with_canonical: int
    eligible_alias_rows: int
    aliases_seeded: int
    unique_aliases: int
    unique_concepts: int
    duplicate_raw_expressions: int
    duplicate_normalized_expressions: int
    same_expression_multiple_canonical: int
    skipped_rows: int
    skip_reason_counts: dict[str, int]
    semantic_roles: tuple[SemanticRoleProfile, ...]


@dataclass(frozen=True)
class SemanticParityAudit:
    metrics: dict[str, int]
    ambiguous_expressions: tuple[str, ...]
    skip_reason_counts: dict[str, int]


def load_semantic_normalization_v4_seed(path: str | Path) -> SemanticKnowledgeSeed:
    rows = _read_rows(path)
    return build_semantic_knowledge_seed_from_rows(rows, source_path=path)


def build_semantic_knowledge_seed_from_rows(
    rows: tuple[dict[str, str], ...],
    *,
    source_path: str | Path,
) -> SemanticKnowledgeSeed:
    eligible_rows = tuple(row for row in rows if _is_alias_seed_candidate(row))
    concept_scopes: dict[str, set[str]] = defaultdict(set)
    for row in eligible_rows:
        concept_scopes[_clean(row.get("canonical_service"))].add(
            _clean(row.get("market_scope"))
        )

    concepts = tuple(
        SemanticConcept(
            concept_id=concept_id,
            concept_type=_single_scope(concept_id, concept_scopes[concept_id]),
        )
        for concept_id in sorted(concept_scopes)
    )

    aliases = tuple(
        SemanticAlias(
            expression=_clean(row.get("economic_object_raw")),
            concept_id=_clean(row.get("canonical_service")),
            context=SemanticContext.PROVIDER_OBSERVATION,
            provenance=KnowledgeProvenance(
                origin_type=SEMANTIC_NORMALIZATION_V4_ORIGIN_TYPE,
                origin_reference=_origin_reference(source_path, row),
                origin_version=SEMANTIC_NORMALIZATION_V4_VERSION,
            ),
        )
        for row in sorted(eligible_rows, key=_stable_row_sort_key)
    )
    return SemanticKnowledgeSeed(concepts=concepts, aliases=aliases)


def profile_semantic_normalization_v4(path: str | Path) -> SemanticNormalizationV4Profile:
    rows = _read_rows(path)
    seed = build_semantic_knowledge_seed_from_rows(rows, source_path=path)
    eligible_rows = tuple(row for row in rows if _is_alias_seed_candidate(row))
    skipped_rows = tuple(row for row in rows if not _is_alias_seed_candidate(row))
    skip_reason_counts = Counter(_skip_reason(row) for row in skipped_rows)

    raw_counts = Counter(_clean(row.get("economic_object_raw")) for row in rows)
    normalized_counts = Counter(_fold(row.get("economic_object_raw")) for row in rows)
    by_normalized: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        raw = _clean(row.get("economic_object_raw"))
        canonical = _clean(row.get("canonical_service"))
        if raw and canonical:
            by_normalized[_fold(raw)].add(canonical)

    role_counts = Counter(_clean(row.get("semantic_role")) for row in rows)
    role_with_canonical = Counter(
        _clean(row.get("semantic_role"))
        for row in rows
        if _clean(row.get("canonical_service"))
    )
    semantic_roles = tuple(
        SemanticRoleProfile(
            semantic_role=role,
            rows=role_counts[role],
            with_canonical_service=role_with_canonical[role],
            candidate_for_alias_seed=role in ELIGIBLE_ALIAS_SEMANTIC_ROLES,
            reason=_role_seed_reason(role),
        )
        for role in sorted(role_counts)
    )

    return SemanticNormalizationV4Profile(
        total_rows=len(rows),
        rows_with_canonical=sum(
            1 for row in rows if _clean(row.get("canonical_service"))
        ),
        eligible_alias_rows=len(eligible_rows),
        aliases_seeded=len(seed.aliases),
        unique_aliases=len({_fold(alias.expression) for alias in seed.aliases}),
        unique_concepts=len(seed.concepts),
        duplicate_raw_expressions=sum(
            1 for raw, count in raw_counts.items() if raw and count > 1
        ),
        duplicate_normalized_expressions=sum(
            1 for raw, count in normalized_counts.items() if raw and count > 1
        ),
        same_expression_multiple_canonical=sum(
            1 for canonical_ids in by_normalized.values() if len(canonical_ids) > 1
        ),
        skipped_rows=len(skipped_rows),
        skip_reason_counts=dict(sorted(skip_reason_counts.items())),
        semantic_roles=semantic_roles,
    )


def audit_semantic_normalization_v4_parity(path: str | Path) -> SemanticParityAudit:
    rows = _read_rows(path)
    seed = build_semantic_knowledge_seed_from_rows(rows, source_path=path)
    index = SemanticKnowledgeIndex(concepts=seed.concepts, aliases=seed.aliases)
    metrics = Counter()
    ambiguous_expressions: set[str] = set()

    for row in rows:
        if not _is_alias_seed_candidate(row):
            continue

        expected = _clean(row.get("canonical_service"))
        expression = _clean(row.get("economic_object_raw"))
        resolution = index.resolve(
            expression,
            context=SemanticContext.PROVIDER_OBSERVATION,
        )
        actual = {candidate.concept.concept_id for candidate in resolution.candidates}

        if resolution.status is SemanticResolutionStatus.UNKNOWN:
            metrics["MISSING"] += 1
        elif resolution.status is SemanticResolutionStatus.AMBIGUOUS:
            ambiguous_expressions.add(_fold(expression))
            if expected in actual:
                metrics["AMBIGUOUS_PRESERVED"] += 1
            else:
                metrics["WRONG_CONCEPT"] += 1
        elif actual == {expected}:
            metrics["PARITY"] += 1
        else:
            metrics["WRONG_CONCEPT"] += 1

    for key in ("PARITY", "AMBIGUOUS_PRESERVED", "MISSING", "WRONG_CONCEPT"):
        metrics.setdefault(key, 0)

    skipped_rows = tuple(row for row in rows if not _is_alias_seed_candidate(row))
    return SemanticParityAudit(
        metrics=dict(sorted(metrics.items())),
        ambiguous_expressions=tuple(sorted(ambiguous_expressions)),
        skip_reason_counts=dict(
            sorted(Counter(_skip_reason(row) for row in skipped_rows).items())
        ),
    )


def _read_rows(path: str | Path) -> tuple[dict[str, str], ...]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return tuple(csv.DictReader(f))


def _is_alias_seed_candidate(row: dict[str, str]) -> bool:
    return (
        bool(_clean(row.get("economic_object_raw")))
        and bool(_clean(row.get("canonical_service")))
        and _clean(row.get("semantic_role")) in ELIGIBLE_ALIAS_SEMANTIC_ROLES
    )


def _skip_reason(row: dict[str, str]) -> str:
    if not _clean(row.get("economic_object_raw")):
        return "MISSING_RAW_EXPRESSION"
    if not _clean(row.get("canonical_service")):
        return "MISSING_CANONICAL_SERVICE"
    role = _clean(row.get("semantic_role"))
    if role not in ELIGIBLE_ALIAS_SEMANTIC_ROLES:
        return f"SEMANTIC_ROLE:{role}"
    return "ELIGIBLE"


def _role_seed_reason(role: str) -> str:
    if role in ELIGIBLE_ALIAS_SEMANTIC_ROLES:
        return "single canonical service row with explicit canonical_service"
    return "not a single-service canonical alias row in v4"


def _origin_reference(source_path: str | Path, row: dict[str, str]) -> str:
    source = Path(source_path).as_posix()
    observation_id = _clean(row.get("observation_id"))
    if observation_id:
        return f"{source}:observation_id={observation_id}"
    return f"{source}:row_hash={_row_identity(row)}"


def _row_identity(row: dict[str, str]) -> str:
    fields = (
        _clean(row.get("source")),
        _clean(row.get("economic_object_raw")),
        _clean(row.get("price_value")),
        _clean(row.get("currency")),
        _clean(row.get("semantic_role")),
        _clean(row.get("canonical_service")),
    )
    folded = "|".join(fields)
    return hashlib.sha256(folded.encode("utf-8")).hexdigest()[:16]


def _stable_row_sort_key(row: dict[str, str]) -> tuple[int, str]:
    observation_id = _clean(row.get("observation_id"))
    if observation_id.isdigit():
        return (int(observation_id), "")
    return (10**12, observation_id)


def _single_scope(concept_id: str, scopes: set[str]) -> str:
    clean_scopes = {scope for scope in scopes if scope}
    if len(clean_scopes) != 1:
        raise ValueError(
            f"Cannot derive a single concept_type for {concept_id}: "
            + ", ".join(sorted(clean_scopes))
        )
    return next(iter(clean_scopes))


def _clean(value: object) -> str:
    return str(value or "").strip()


def _fold(text: object) -> str:
    normalized = unicodedata.normalize("NFKD", _clean(text))
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_marks.lower().split())
