import json

from src.infraestructura.economic_dimensions_artifact import (
    build_economic_dimensions_sidecar,
    load_economic_dimensions_sidecar,
)


def test_sidecar_is_deterministic_cardinality_preserving_and_read_only(tmp_path):
    source = tmp_path / "semantic.csv"
    source.write_text(
        "observation_id,source,province,city,economic_object_raw,price_value,currency,semantic_role,market_scope,price_scope,extractor_version\n"
        "1,provider_a,Córdoba,Córdoba,Soporte por hora USD 30,30,ARS,SINGLE_SERVICE,LOCAL_SERVICE,PER_MONTH,v1\n"
        "2,provider_b,,,Servicio sin unidad,200,ARS,SINGLE_SERVICE,UNKNOWN,,v1\n",
        encoding="utf-8",
    )
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "source,provider,url\n"
        "provider_a,Provider A,https://example.test/a\n"
        "provider_b,Provider B,https://example.test/b\n",
        encoding="utf-8",
    )
    before = source.read_bytes()
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"

    metrics_a = build_economic_dimensions_sidecar(source, registry, first, version="test-v1")
    metrics_b = build_economic_dimensions_sidecar(source, registry, second, version="test-v1")

    assert source.read_bytes() == before
    assert first.read_bytes() == second.read_bytes()
    assert metrics_a == metrics_b
    assert metrics_a["TOTAL_OBSERVATIONS"] == 2
    assert metrics_a["OUTPUT_ROWS"] == 2
    assert metrics_a["CONFLICTED_DIMENSIONS"]["price_scope"] == 1
    assert metrics_a["CONFLICTED_DIMENSIONS"]["currency"] == 1
    assert metrics_a["EXPLICIT_DIMENSIONS"] == metrics_a["OBSERVED_DIMENSIONS"]

    loaded = load_economic_dimensions_sidecar(first)
    assert set(loaded) == {"1", "2"}
    assert loaded["1"].price_scope.status.value == "CONFLICTED"
    assert loaded["1"].currency.status.value == "CONFLICTED"

    payloads = [json.loads(line) for line in first.read_text(encoding="utf-8").splitlines()]
    assert [payload["observation_id"] for payload in payloads] == ["1", "2"]
    assert all(payload["schema_version"] == "economic-evidence-dimensions-v1" for payload in payloads)
