import hashlib
import json
from pathlib import Path

from src.infraestructura.knowledge_candidate_artifact import build_knowledge_candidate_artifacts


ROOT = Path(__file__).parents[1]


def build(tmp_path, prefix):
    outputs = {
        "audit": tmp_path / f"{prefix}.audit.json",
        "candidates": tmp_path / f"{prefix}.candidates.jsonl",
        "summary": tmp_path / f"{prefix}.summary.json",
        "requests": tmp_path / f"{prefix}.requests.jsonl",
        "plans": tmp_path / f"{prefix}.plans.jsonl",
        "alignment": tmp_path / f"{prefix}.alignment.json",
    }
    metrics = build_knowledge_candidate_artifacts(ROOT, **outputs)
    return metrics, outputs


def test_real_candidate_artifacts_are_deterministic_and_evidence_backed(tmp_path):
    first_metrics, first = build(tmp_path, "one")
    second_metrics, second = build(tmp_path, "two")

    assert first_metrics == second_metrics
    for key in first:
        assert first[key].read_bytes() == second[key].read_bytes()
    candidates = [json.loads(line) for line in first["candidates"].read_text(encoding="utf-8").splitlines()]
    assert candidates
    assert all(item["runtime_effect"] is False for item in candidates)
    assert all(item["supporting_evidence"] for item in candidates)
    assert all(item["candidate_id"].startswith("knowledge-candidate:") for item in candidates)
    assert any(item["contradicting_evidence"] for item in candidates)
    assert any(item["evidence_summary"]["raw_evidence_count"] for item in candidates)
    assert any(item["evidence_summary"]["normalized_evidence_count"] for item in candidates)


def test_evidence_requests_are_ranked_explainable_and_never_execute(tmp_path):
    _, outputs = build(tmp_path, "artifact")
    requests = [json.loads(line) for line in outputs["requests"].read_text(encoding="utf-8").splitlines()]

    assert [item["rank"] for item in requests] == list(range(1, len(requests) + 1))
    assert all(item["execute_automatically"] is False for item in requests)
    assert all(item["score_breakdown"] for item in requests)


def test_generation_does_not_mutate_raw_normalization_parser_pricing_or_api(tmp_path):
    protected = (
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "src/aplicacion/semantic_normalization_live.py",
        ROOT / "src/infraestructura/semantic_knowledge_seed.py",
        ROOT / "src/aplicacion/parser_consulta_pricing.py",
        ROOT / "src/aplicacion/enki_pricing_query_service.py",
        ROOT / "src/api/main.py",
    )
    raw_files = tuple(path for path in (ROOT / "data/raw").rglob("*") if path.is_file())
    assert all(path.exists() for path in protected)
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected + raw_files}

    build(tmp_path, "firewall")

    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected + raw_files} == before


def test_real_currency_conflicts_159_to_161_remain_contradictory(tmp_path):
    _, outputs = build(tmp_path, "currency")
    candidates = [json.loads(line) for line in outputs["candidates"].read_text(encoding="utf-8").splitlines()]
    conflict = next(item for item in candidates if item["proposed_knowledge"] == "currency marker 'u$s' may indicate currency=USD")

    assert {item["observation_id"] for item in conflict["supporting_evidence"]} == {"159", "160", "161"}
    assert {item["value"] for item in conflict["contradicting_evidence"]} == {"ARS"}
    assert conflict["epistemic_status"] == "CONFLICTED"
    assert conflict["validation_readiness"] == "CONFLICTED"


def test_alignment_audit_proves_learning_is_shadow_only(tmp_path):
    _, outputs = build(tmp_path, "alignment")
    alignment = json.loads(outputs["alignment"].read_text(encoding="utf-8"))

    assert alignment["ENTENDER"]["unknown_preserved"] is True
    assert alignment["CONECTAR"]["candidate_evidence_links"] is True
    assert alignment["APRENDER"]["auto_promotion"] is False
    assert alignment["EXPLOTAR"]["new_public_economic_decision"] is False
