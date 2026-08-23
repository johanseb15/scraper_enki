import hashlib
import json
from pathlib import Path

from src.infraestructura.candidate_shadow_validation_runner import run_candidate_shadow_validation


ROOT = Path(__file__).parents[1]
CANDIDATE_ID = "knowledge-candidate:3190e09c277a38b6330d"


def run(tmp_path, prefix):
    outputs = {
        "audit_path": tmp_path / f"{prefix}.audit.json",
        "dataset_path": tmp_path / f"{prefix}.dataset.jsonl",
        "results_path": tmp_path / f"{prefix}.results.jsonl",
        "summary_path": tmp_path / f"{prefix}.summary.json",
        "requests_path": tmp_path / f"{prefix}.requests.jsonl",
    }
    metrics = run_candidate_shadow_validation(ROOT, candidate_id=CANDIDATE_ID, **outputs)
    return metrics, outputs


def test_real_validation_is_deterministic_and_separates_support_from_controls(tmp_path):
    first_metrics, first = run(tmp_path, "one")
    second_metrics, second = run(tmp_path, "two")

    assert first_metrics == second_metrics
    for key in first:
        assert first[key].read_bytes() == second[key].read_bytes()
    cases = [json.loads(line) for line in first["dataset_path"].read_text(encoding="utf-8").splitlines()]
    assert sum(item["partition"] == "SUPPORT" for item in cases) == 5
    assert sum(item["partition"] == "HOLDOUT" for item in cases) == 3
    assert not ({item["case_id"] for item in cases if item["partition"] == "SUPPORT"} &
                {item["case_id"] for item in cases if item["partition"] == "HOLDOUT"})
    assert {item["expected_condition"] for item in cases if item["partition"] == "HOLDOUT"} == {
        "EXPLICIT_INCLUDED", "EXPLICIT_EXCLUDED", "UNKNOWN"
    }


def test_real_candidate_needs_in_scope_independent_holdout(tmp_path):
    metrics, outputs = run(tmp_path, "real")
    result = json.loads(outputs["results_path"].read_text(encoding="utf-8").splitlines()[0])

    assert metrics["VALIDATION_OUTCOME"] == "NEEDS_MORE_EVIDENCE"
    assert metrics["TOTAL_VALIDATION_CASES"] == 8
    assert metrics["SUPPORT_CASES"] == 5
    assert metrics["HOLDOUT_CASES"] == 3
    assert metrics["UNIQUE_VALIDATION_PROVIDERS"] == 0
    assert metrics["UNIQUE_VALIDATION_SOURCES"] == 0
    assert metrics["NEGATIVE_CONTROLS"] == 3
    assert result["runtime_effect"] is False
    assert result["promotion_authorized"] is False
    assert result["false_positives"] == 0
    assert result["scope_violations"] == 0


def test_validation_request_is_exact_and_never_executes(tmp_path):
    _, outputs = run(tmp_path, "request")
    request = json.loads(outputs["requests_path"].read_text(encoding="utf-8").splitlines()[0])

    assert request["required_independent_providers"] == 2
    assert request["required_independent_sources"] == 2
    assert request["required_evidence_type"] == "NEW_TARGETED_ACQUISITION_OUTCOME_WITH_REPRODUCIBLE_RAW"
    assert request["execute_automatically"] is False


def test_runner_preserves_existing_history_and_is_idempotent(tmp_path):
    _, outputs = run(tmp_path, "history")
    before = outputs["results_path"].read_bytes()

    run_candidate_shadow_validation(
        ROOT, candidate_id=CANDIDATE_ID,
        audit_path=outputs["audit_path"], dataset_path=outputs["dataset_path"],
        results_path=outputs["results_path"], summary_path=outputs["summary_path"],
        requests_path=outputs["requests_path"],
    )

    assert outputs["results_path"].read_bytes() == before
    assert len(outputs["results_path"].read_text(encoding="utf-8").splitlines()) == 1


def test_real_run_mutates_no_candidate_raw_parser_pricing_api_or_currency_conflict(tmp_path):
    protected = (
        ROOT / "data/knowledge_candidates_v1.jsonl",
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/economic_dimensions_v2.jsonl",
        ROOT / "src/aplicacion/parser_consulta_pricing.py",
        ROOT / "src/aplicacion/enki_pricing_query_service.py",
        ROOT / "src/api/main.py",
    )
    raw = tuple(path for path in (ROOT / "data/raw").rglob("*") if path.is_file())
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected + raw}

    run(tmp_path, "firewall")

    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected + raw} == before
    dimensions = [json.loads(line) for line in (ROOT / "data/economic_dimensions_v2.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(dimensions[index - 1]["dimensions"]["currency"]["status"] == "CONFLICTED" for index in (159, 160, 161))
