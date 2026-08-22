import json

from scripts.build_economic_dimensions import build_economic_dimensions_sidecar
from scripts.build_semantic_economic_shadow import build_semantic_economic_shadow
from src.infraestructura.economic_dimensions_v2_artifact import (
    build_economic_dimensions_v2_sidecar,
)


def test_enriched_shadow_reports_conflicts_and_preserves_indexed_candidates(tmp_path):
    source = tmp_path / "semantic.csv"
    source.write_text(
        "observation_id,source,province,city,economic_object_raw,price_value,currency,semantic_role,market_scope,price_scope,extractor_version\n"
        "1,provider_a,Córdoba,Córdoba,Soporte por hora USD 30,30,ARS,SINGLE_SERVICE,LOCAL_SERVICE,PER_MONTH,v1\n"
        "2,provider_b,Córdoba,Córdoba,Soporte por hora,200,ARS,SINGLE_SERVICE,LOCAL_SERVICE,PER_HOUR,v1\n",
        encoding="utf-8",
    )
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "source,provider,url\n"
        "provider_a,Provider A,https://example.test/a\n"
        "provider_b,Provider B,https://example.test/b\n",
        encoding="utf-8",
    )
    dimensions = tmp_path / "dimensions.jsonl"
    build_economic_dimensions_sidecar(source, registry, dimensions, version="test-v1")

    shadow = tmp_path / "shadow.jsonl"
    metrics = build_semantic_economic_shadow(
        source,
        shadow,
        version="test-enriched-v1",
        dimensions_path=dimensions,
    )

    assert metrics["CONFLICTED_DIMENSIONS"]["currency"] == 1
    assert metrics["CONFLICTED_DIMENSIONS"]["price_scope"] == 1
    assert metrics["CANDIDATE_PAIRS_AFTER_INDEX"] <= metrics["CANDIDATE_PAIRS_BEFORE_INDEX"]
    assert metrics["CANDIDATE_RESULTS"] == metrics["TOTAL_CANDIDATE_EVIDENCE"]
    rows = [json.loads(line) for line in shadow.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["conflicted_dimensions"] == ["price_scope", "currency"]


def test_v2_shadow_reports_cardinality_migration_and_keeps_candidate_index(tmp_path):
    source = tmp_path / "semantic.csv"
    source.write_text(
        "observation_id,source,province,city,economic_object_raw,price_value,currency,semantic_role,market_scope,extractor_version\n"
        "1,provider_a,Córdoba,Córdoba,Soporte remoto por hora,100,ARS,SINGLE_SERVICE,REMOTE_NATIONAL_SERVICE,v1\n"
        "2,provider_b,Córdoba,Córdoba,Urgencia fuera de horario por hora,200,ARS,SINGLE_SERVICE,LOCAL_SERVICE,v1\n"
        "3,provider_c,Córdoba,Córdoba,Ticket USD 30 por hora,30,ARS,SINGLE_SERVICE,LOCAL_SERVICE,v1\n",
        encoding="utf-8",
    )
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "source,provider,url\nprovider_a,A,x\nprovider_b,B,y\nprovider_c,C,z\n",
        encoding="utf-8",
    )
    v1 = tmp_path / "v1.jsonl"
    v2 = tmp_path / "v2.jsonl"
    build_economic_dimensions_sidecar(source, registry, v1)
    build_economic_dimensions_v2_sidecar(
        source, registry, v2, previous_dimensions_path=v1
    )

    metrics = build_semantic_economic_shadow(
        source,
        tmp_path / "shadow.jsonl",
        dimensions_path=v2,
        previous_dimensions_path=v1,
    )

    assert metrics["FALSE_CONFLICTS_REMOVED"] == 2
    assert metrics["REAL_CONFLICTS_PRESERVED"] == 1
    assert metrics["MULTIVALUE_CONTEXTS"] == 1
    assert metrics["ORTHOGONAL_DIMENSION_SPLITS"] == 1
    assert metrics["CONFLICTS_BY_DIMENSION"] == {"currency": 1}
    assert metrics["AMBIGUITIES_BY_DIMENSION"] == {}
    assert metrics["CANDIDATE_PAIRS_AFTER_INDEX"] <= metrics["CANDIDATE_PAIRS_BEFORE_INDEX"]
