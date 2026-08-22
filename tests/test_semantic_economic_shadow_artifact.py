import json

from scripts.build_semantic_economic_shadow import build_semantic_economic_shadow


def test_shadow_artifact_is_deterministic_read_only_and_reports_metrics(tmp_path):
    source = tmp_path / "semantic.csv"
    source.write_text(
        "observation_id,source,province,city,economic_object_raw,price_value,currency,semantic_role,market_scope,matched_services,canonical_service,comparability_key,original_comparable_status,extractor_version\n"
        "1,provider_a,Córdoba,,Soporte remoto por hora,100,ARS,SINGLE_SERVICE,LOCAL_SERVICE,SOPORTE_REMOTO,SOPORTE_REMOTO,Córdoba::SOPORTE_REMOTO,INDETERMINATE,v1\n"
        "2,provider_b,Córdoba,,Soporte remoto mensual,200,ARS,SINGLE_SERVICE,LOCAL_SERVICE,SOPORTE_REMOTO,SOPORTE_REMOTO,Córdoba::SOPORTE_REMOTO,INDETERMINATE,v1\n"
        "3,provider_c,Córdoba,,Precio por hora,0,ARS,PRICE_CONTEXT,NONE,,,,INDETERMINATE,v1\n",
        encoding="utf-8",
    )
    before = source.read_bytes()
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"

    metrics_a = build_semantic_economic_shadow(source, first, version="test-v1")
    metrics_b = build_semantic_economic_shadow(source, second, version="test-v1")

    assert source.read_bytes() == before
    assert first.read_bytes() == second.read_bytes()
    assert metrics_a == metrics_b
    assert metrics_a["TOTAL_OBSERVATIONS"] == 3
    assert metrics_a["TOTAL_CANDIDATE_EVIDENCE"] >= 3
    assert metrics_a["TOTAL_EXCLUDED_EVIDENCE"] >= 1
    assert metrics_a["EXCLUSION_REASONS"]["CADENCE_MISMATCH"] == 2

    rows = [json.loads(line) for line in first.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    assert rows[0]["observation_id"] == "1"
    assert rows[0]["version"] == "test-v1"
    assert "recommended_price" not in rows[0]
    assert "decision_label" not in rows[0]
    assert rows[2]["readiness"] == "INSUFFICIENT"
