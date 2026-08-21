import csv
from pathlib import Path

from src.dominio.semantic_knowledge import (
    SemanticContext,
    SemanticKnowledgeIndex,
    SemanticResolutionStatus,
)
from src.aplicacion import parser_consulta_pricing
from src.infraestructura.semantic_knowledge_seed import (
    ELIGIBLE_ALIAS_SEMANTIC_ROLES,
    SEMANTIC_NORMALIZATION_V4_VERSION,
    audit_semantic_normalization_v4_parity,
    build_semantic_knowledge_seed_from_rows,
    load_semantic_normalization_v4_seed,
    profile_semantic_normalization_v4,
)

CSV_PATH = Path("data/semantic_normalization_v4.csv")


def _rows():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        return tuple(csv.DictReader(f))


def test_canonical_concepts_can_be_seeded_from_current_enki_authority():
    seed = load_semantic_normalization_v4_seed(CSV_PATH)

    concept_ids = {concept.concept_id for concept in seed.concepts}

    assert len(seed.concepts) == 25
    assert "FORMATEO_INSTALACION_SO" in concept_ids
    assert "LIMPIEZA_MANTENIMIENTO" in concept_ids
    assert "SOPORTE_REMOTO" in concept_ids
    assert "DIAGNOSTICO_REVISION" in concept_ids
    assert "BACKUP_DATOS" in concept_ids
    assert "RECUPERACION_DATOS" in concept_ids
    assert "ARMADO_PC" in concept_ids
    assert seed.concept_by_id("SOPORTE_REMOTO").concept_type == "REMOTE_NATIONAL_SERVICE"
    assert seed.concept_by_id("FORMATEO_INSTALACION_SO").concept_type == "LOCAL_SERVICE"


def test_semantic_normalization_v4_known_mapping_becomes_provider_alias():
    seed = load_semantic_normalization_v4_seed(CSV_PATH)
    index = SemanticKnowledgeIndex(concepts=seed.concepts, aliases=seed.aliases)

    resolution = index.resolve(
        "Servicio realizado a distancia.",
        context=SemanticContext.PROVIDER_OBSERVATION,
    )

    assert resolution.status is SemanticResolutionStatus.RESOLVED
    assert resolution.candidates[0].concept.concept_id == "SOPORTE_REMOTO"
    assert resolution.candidates[0].alias.context is SemanticContext.PROVIDER_OBSERVATION


def test_seeded_alias_preserves_exact_canonical_service():
    seed = load_semantic_normalization_v4_seed(CSV_PATH)

    alias = next(
        alias
        for alias in seed.aliases
        if alias.expression == "Diagnostico / Revisión PC-Notebook-AIO"
    )

    assert alias.concept_id == "DIAGNOSTICO_REVISION"


def test_seeded_alias_preserves_row_level_provenance():
    seed = load_semantic_normalization_v4_seed(CSV_PATH)

    alias = next(
        alias
        for alias in seed.aliases
        if alias.expression == "Servicio realizado a distancia."
    )

    assert alias.provenance.origin_type == "SEMANTIC_NORMALIZATION_V4"
    assert alias.provenance.origin_reference == (
        "data/semantic_normalization_v4.csv:observation_id=43"
    )
    assert alias.provenance.origin_version == SEMANTIC_NORMALIZATION_V4_VERSION


def test_row_without_canonical_service_does_not_invent_alias():
    row = next(row for row in _rows() if row["observation_id"] == "1")
    seed = build_semantic_knowledge_seed_from_rows((row,), source_path=CSV_PATH)

    assert seed.concepts == ()
    assert seed.aliases == ()


def test_non_service_semantic_role_does_not_become_service_alias():
    row = next(row for row in _rows() if row["semantic_role"] == "SCOPE_DEVICE")
    assert row["semantic_role"] not in ELIGIBLE_ALIAS_SEMANTIC_ROLES

    seed = build_semantic_knowledge_seed_from_rows((row,), source_path=CSV_PATH)

    assert seed.aliases == ()


def test_same_expression_mapping_to_different_concepts_remains_ambiguous():
    rows = (
        {
            "observation_id": "a",
            "economic_object_raw": "servicio compartido",
            "semantic_role": "SINGLE_SERVICE",
            "market_scope": "LOCAL_SERVICE",
            "canonical_service": "DIAGNOSTICO_REVISION",
        },
        {
            "observation_id": "b",
            "economic_object_raw": "servicio compartido",
            "semantic_role": "SINGLE_SERVICE",
            "market_scope": "LOCAL_SERVICE",
            "canonical_service": "REPARACION_HARDWARE",
        },
    )
    seed = build_semantic_knowledge_seed_from_rows(rows, source_path=CSV_PATH)
    index = SemanticKnowledgeIndex(concepts=seed.concepts, aliases=seed.aliases)

    resolution = index.resolve(
        "servicio compartido",
        context=SemanticContext.PROVIDER_OBSERVATION,
    )

    assert resolution.status is SemanticResolutionStatus.AMBIGUOUS
    assert {candidate.concept.concept_id for candidate in resolution.candidates} == {
        "DIAGNOSTICO_REVISION",
        "REPARACION_HARDWARE",
    }


def test_duplicate_identical_alias_mappings_are_deterministic():
    rows = (
        {
            "observation_id": "2",
            "economic_object_raw": "revision pc",
            "semantic_role": "SINGLE_SERVICE",
            "market_scope": "LOCAL_SERVICE",
            "canonical_service": "DIAGNOSTICO_REVISION",
        },
        {
            "observation_id": "1",
            "economic_object_raw": "revision pc",
            "semantic_role": "SINGLE_SERVICE",
            "market_scope": "LOCAL_SERVICE",
            "canonical_service": "DIAGNOSTICO_REVISION",
        },
    )

    seed = build_semantic_knowledge_seed_from_rows(rows, source_path=CSV_PATH)
    index = SemanticKnowledgeIndex(concepts=seed.concepts, aliases=seed.aliases)
    resolution = index.resolve("revision pc", context=SemanticContext.PROVIDER_OBSERVATION)

    assert resolution.status is SemanticResolutionStatus.RESOLVED
    assert [alias.provenance.origin_reference for alias in seed.aliases] == [
        "data/semantic_normalization_v4.csv:observation_id=1",
        "data/semantic_normalization_v4.csv:observation_id=2",
    ]
    assert [candidate.provenance.origin_reference for candidate in resolution.candidates] == [
        "data/semantic_normalization_v4.csv:observation_id=1",
        "data/semantic_normalization_v4.csv:observation_id=2",
    ]


def test_seed_process_is_idempotent():
    first = load_semantic_normalization_v4_seed(CSV_PATH)
    second = load_semantic_normalization_v4_seed(CSV_PATH)

    assert first == second


def test_seed_does_not_require_pricing_data():
    seed = build_semantic_knowledge_seed_from_rows(
        (
            {
                "observation_id": "1",
                "economic_object_raw": "revision pc",
                "semantic_role": "SINGLE_SERVICE",
                "market_scope": "LOCAL_SERVICE",
                "canonical_service": "DIAGNOSTICO_REVISION",
            },
        ),
        source_path=CSV_PATH,
    )

    assert len(seed.aliases) == 1
    assert not hasattr(seed, "price")
    assert not hasattr(seed, "pricing_evidence")


def test_seed_does_not_mutate_production_mappings():
    before = tuple(parser_consulta_pricing.RULES)

    load_semantic_normalization_v4_seed(CSV_PATH)

    assert tuple(parser_consulta_pricing.RULES) == before


def test_profile_and_parity_audit_match_current_csv_without_wrong_concepts():
    profile = profile_semantic_normalization_v4(CSV_PATH)
    audit = audit_semantic_normalization_v4_parity(CSV_PATH)

    assert profile.total_rows == 273
    assert profile.rows_with_canonical == 84
    assert profile.eligible_alias_rows == 84
    assert profile.skipped_rows == 189
    assert audit.metrics["WRONG_CONCEPT"] == 0
    assert audit.metrics["MISSING"] == 0
    assert audit.metrics["PARITY"] == 84

def test_seed_fallback_provenance_is_deterministic_without_observation_id():
    base_row = {
        "economic_object_raw": "revision pc",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "LOCAL_SERVICE",
        "canonical_service": "DIAGNOSTICO_REVISION",
        "source": "fixture_source",
        "price_value": "1000",
        "currency": "ARS",
    }
    same_row = dict(base_row)
    changed_row = {
        **base_row,
        "economic_object_raw": "diagnostico notebook",
    }

    first = build_semantic_knowledge_seed_from_rows((base_row,), source_path=CSV_PATH)
    second = build_semantic_knowledge_seed_from_rows((same_row,), source_path=CSV_PATH)
    changed = build_semantic_knowledge_seed_from_rows((changed_row,), source_path=CSV_PATH)

    first_reference = first.aliases[0].provenance.origin_reference
    second_reference = second.aliases[0].provenance.origin_reference
    changed_reference = changed.aliases[0].provenance.origin_reference

    assert ":row_hash=" in first_reference
    assert first_reference == second_reference
    assert changed_reference != first_reference
