import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_full_product_e2e_artifact_is_honest_and_complete():
    artifact = json.loads((ROOT / "data/e2e/full_product_e2e_v1.json").read_text(encoding="utf-8"))
    assert artifact["overall_outcome"] == "PASS_WITH_KNOWN_DEBT"
    assert artifact["failures"] == []
    assert artifact["human_real_001_summary"]["field_data_preserved"] is True
    assert artifact["human_real_001_summary"]["mutated"] is False
    assert artifact["corpus_summary"]["total"] == 50
    assert artifact["corpus_summary"]["wrong_interpretation"] == 21
    assert artifact["readiness_coverage"]["DECISION_READY"] == 0
    assert artifact["knowledge_safety"]["outcome"] == "FAIL_SHADOW_VALIDATION"
    assert artifact["knowledge_safety"]["auto_promotions"] == 0
    assert artifact["knowledge_safety"]["runtime_writes"] == 0
    assert artifact["no_promotion"] is True
    assert artifact["no_runtime_learning"] is True
