import json

from scripts.build_economic_dimensions import build_economic_dimensions_sidecar
from scripts.build_semantic_economic_shadow import build_semantic_economic_shadow


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
