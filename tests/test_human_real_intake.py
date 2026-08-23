import json

from src.infraestructura.human_real_intake import (
    append_founder_feedback,
    field_coverage,
    ingest_human_real_case,
)


def ingest(tmp_path, **feedback):
    return ingest_human_real_case(
        case_path=tmp_path / "cases.jsonl", trace_path=tmp_path / "traces.jsonl",
        raw_user_input="me quieren cobrar 35 lucas por soporte remoto, está bien?",
        case_id="founder:001", received_at="2026-08-23T12:00:00-03:00",
        local_cohortes=(), remote_cohortes=(), **feedback,
    )


def test_human_real_is_append_only_preserves_raw_and_runs_real_pipeline(tmp_path):
    trace, case = ingest(tmp_path, founder_note="primer caso")
    ingest(tmp_path, founder_note="primer caso")
    assert trace.case_origin == "HUMAN_REAL"
    assert trace.raw_user_input == case["raw_user_input"]
    assert trace.parser_result["canonical_services"] == ["SOPORTE_REMOTO"]
    assert len((tmp_path / "cases.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    assert len((tmp_path / "traces.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_founder_expectation_is_feedback_not_truth_or_promotion(tmp_path):
    trace, case = ingest(tmp_path, expected_intent="MARKET_REFERENCE", expected_normalization={"price.value": 1})
    assert trace.intent_result["action"] == "EVALUATE_PRICE"
    assert case["founder_feedback"]["expected_intent"] == "MARKET_REFERENCE"
    assert case["founder_feedback"]["epistemic_role"] == "HUMAN_FEEDBACK_NOT_PROMOTED_TRUTH"
    assert case["promotion_authorized"] is False


def test_feedback_is_multilabel_append_only_and_never_promotes(tmp_path):
    event = append_founder_feedback(
        tmp_path / "feedback.jsonl", trace_id="trace:1", received_at="2026-08-23T13:00:00-03:00",
        labels=("WRONG", "MISSING_CONTEXT"), note="faltó provincia",
    )
    append_founder_feedback(
        tmp_path / "feedback.jsonl", trace_id="trace:1", received_at="2026-08-23T13:00:00-03:00",
        labels=("MISSING_CONTEXT", "WRONG"), note="faltó provincia",
    )
    assert event["labels"] == ["MISSING_CONTEXT", "WRONG"]
    assert event["promotion_authorized"] is False
    assert len((tmp_path / "feedback.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_explicit_normalization_recall_requires_human_review(tmp_path):
    trace, unreviewed = ingest(tmp_path)
    assert field_coverage(unreviewed, trace)["explicit_normalization_recall"] is None
    reviewed = dict(unreviewed)
    reviewed["founder_feedback"] = {**reviewed["founder_feedback"], "expected_normalization": {"price.value": 35000, "canonical_services": ["SOPORTE_REMOTO"]}}
    coverage = field_coverage(reviewed, trace)
    assert coverage["ground_truth_reviewed"] is True
    assert coverage["explicit_normalization_recall"] == 1.0
