import json

from src.infraestructura.economic_dimensions_artifact import (
    build_economic_dimensions_sidecar,
)
from src.infraestructura.economic_dimensions_loader import (
    load_versioned_economic_dimensions_sidecar,
)
from src.infraestructura.economic_dimensions_v2_artifact import (
    build_economic_dimensions_v2_sidecar,
    load_economic_dimensions_v2_sidecar,
)


def _inputs(tmp_path):
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
        "source,provider,url\n"
        "provider_a,Provider A,https://example.test/a\n"
        "provider_b,Provider B,https://example.test/b\n"
        "provider_c,Provider C,https://example.test/c\n",
        encoding="utf-8",
    )
    return source, registry


def test_v2_sidecar_is_deterministic_reversible_and_preserves_v1(tmp_path):
    source, registry = _inputs(tmp_path)
    v1 = tmp_path / "dimensions-v1.jsonl"
    build_economic_dimensions_sidecar(source, registry, v1, version="fixture-v1")
    v1_before = v1.read_bytes()
    source_before = source.read_bytes()
    first = tmp_path / "dimensions-v2-a.jsonl"
    second = tmp_path / "dimensions-v2-b.jsonl"

    metrics_a = build_economic_dimensions_v2_sidecar(
        source, registry, first, version="fixture-v2", previous_dimensions_path=v1
    )
    metrics_b = build_economic_dimensions_v2_sidecar(
        source, registry, second, version="fixture-v2", previous_dimensions_path=v1
    )

    assert first.read_bytes() == second.read_bytes()
    assert metrics_a == metrics_b
    assert source.read_bytes() == source_before
    assert v1.read_bytes() == v1_before
    assert metrics_a["TOTAL_OBSERVATIONS"] == 3
    assert metrics_a["OUTPUT_ROWS"] == 3
    assert metrics_a["FALSE_CONFLICTS_REMOVED"] == 2
    assert metrics_a["REAL_CONFLICTS_PRESERVED"] == 1
    assert metrics_a["MULTIVALUE_CONTEXTS"] == 1
    assert metrics_a["ORTHOGONAL_DIMENSION_SPLITS"] == 1
    assert metrics_a["CONFLICTS_BY_DIMENSION"] == {"currency": 1}
    assert metrics_a["AMBIGUITIES_BY_DIMENSION"] == {}

    loaded = load_economic_dimensions_v2_sidecar(first)
    assert set(loaded) == {"1", "2", "3"}
    assert loaded["1"].delivery_mode.value == "REMOTE"
    assert loaded["1"].geographic_reach.status.value == "UNKNOWN"
    assert loaded["2"].commercial_context.value == frozenset({"URGENCY", "AFTER_HOURS"})
    assert loaded["3"].currency.status.value == "CONFLICTED"

    payloads = [json.loads(line) for line in first.read_text(encoding="utf-8").splitlines()]
    assert all(item["schema_version"] == "economic-evidence-dimensions-v2" for item in payloads)
    assert [item["observation_id"] for item in payloads] == ["1", "2", "3"]


def test_versioned_loader_accepts_v1_and_v2_without_domain_scattering(tmp_path):
    source, registry = _inputs(tmp_path)
    v1 = tmp_path / "v1.jsonl"
    v2 = tmp_path / "v2.jsonl"
    build_economic_dimensions_sidecar(source, registry, v1)
    build_economic_dimensions_v2_sidecar(source, registry, v2)

    loaded_v1 = load_versioned_economic_dimensions_sidecar(v1)
    loaded_v2 = load_versioned_economic_dimensions_sidecar(v2)

    assert type(loaded_v1["1"]).__name__ == "EconomicEvidenceDimensions"
    assert type(loaded_v2["1"]).__name__ == "EconomicEvidenceDimensionsV2"


def test_v2_summary_audit_preserves_claim_values_basis_origin_and_provenance(tmp_path):
    source, registry = _inputs(tmp_path)
    output = tmp_path / "v2.jsonl"
    build_economic_dimensions_v2_sidecar(source, registry, output)
    summary = json.loads(output.with_suffix(".summary.json").read_text(encoding="utf-8"))

    conflict = summary["metrics"]["CONFLICT_AUDIT"]["currency"][0]
    assert conflict["observation_id"] == "3"
    assert set(conflict["values"]) == {"ARS", "USD"}
    assert conflict["raw_expression"] == "Ticket USD 30 por hora"
    assert {item["origin"] for item in conflict["claims"]} == {
        "NORMALIZED_FIELD",
        "RAW_SOURCE_OBSERVATION",
    }
    assert all(item["raw_basis"] and item["provenance"] for item in conflict["claims"])
