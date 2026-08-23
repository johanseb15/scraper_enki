import hashlib
import json
from pathlib import Path

from src.infraestructura.candidate_validation_evidence_acquisition import (
    acquire_candidate_validation_evidence,
    classify_control,
    classify_snapshot,
    deduplicate_actions,
    versioned_snapshot_path,
)


ROOT = Path(__file__).parents[1]
CANDIDATE_ID = "knowledge-candidate:3190e09c277a38b6330d"


def _run(tmp_path, prefix="run"):
    output = tmp_path / prefix
    return acquire_candidate_validation_evidence(ROOT, output, candidate_id=CANDIDATE_ID), output


def test_snapshot_history_preserves_bytes_and_versions_changes(tmp_path):
    old = b"historical exact bytes"
    assert classify_snapshot(hashlib.sha256(old).hexdigest(), old) == "UNCHANGED"
    assert classify_snapshot(hashlib.sha256(old).hexdigest(), b"new exact bytes") == "CHANGED"
    assert classify_snapshot(None, old) == "NEW"
    path = versioned_snapshot_path(tmp_path, "source:a", b"new exact bytes", ".html")
    assert path.name == hashlib.sha256(b"new exact bytes").hexdigest() + ".html"
    assert not path.exists()


def test_requests_are_deduplicated_without_provider_independence_inflation():
    actions = [
        {"action_id": "a", "url": "https://example.test/a", "source_id": "s", "provider_id": "p"},
        {"action_id": "b", "url": "https://example.test/a", "source_id": "s", "provider_id": "p"},
        {"action_id": "c", "url": "https://example.test/b", "source_id": "s", "provider_id": "p"},
    ]
    assert [item["action_id"] for item in deduplicate_actions(actions)] == ["a", "c"]


def test_control_semantics_require_offer_attribution_and_do_not_treat_absence_as_false():
    assert classify_control(status="OBSERVED", value=True, attribution="OFFER_EXACT", complete=True) == "EXPLICIT_INCLUDED"
    assert classify_control(status="OBSERVED", value=False, attribution="OFFER_EXACT", complete=True) == "EXPLICIT_EXCLUDED"
    assert classify_control(status="UNKNOWN", value=None, attribution="OFFER_EXACT", complete=True) == "GENUINELY_UNKNOWN"
    assert classify_control(status="UNKNOWN", value=None, attribution="PAGE_LEVEL", complete=True) == "AMBIGUOUS_ATTRIBUTION"
    assert classify_control(status="UNKNOWN", value=None, attribution="OFFER_EXACT", complete=False) == "GENUINELY_UNKNOWN"
    assert classify_control(status="NOT_FOUND", value=None, attribution="OFFER_EXACT", complete=True) == "NO_EXPLICIT_EVIDENCE"


def test_real_local_replay_closes_gap_without_network_and_is_deterministic(tmp_path):
    first, first_dir = _run(tmp_path, "one")
    second, second_dir = _run(tmp_path, "two")

    assert first == second
    assert first["PLANNED_ACTIONS"] == 2
    assert first["EXECUTED_ACTIONS"] == 2
    assert first["NETWORK_REQUESTS"] == 0
    assert first["SUCCESS"] == 2
    assert first["UNCHANGED"] == 2
    assert first["VALIDATION_OUTCOME"] == "FAIL_SHADOW_VALIDATION"
    assert first["FALSE_POSITIVES"] == 2
    for name in sorted(path.name for path in first_dir.iterdir()):
        assert (first_dir / name).read_bytes() == (second_dir / name).read_bytes()


def test_dataset_v1_candidate_and_runtime_are_immutable_and_v2_has_independent_controls(tmp_path):
    protected = (
        ROOT / "data/candidate_shadow_validation_dataset_v1.jsonl",
        ROOT / "data/knowledge_candidates_v1.jsonl",
        ROOT / "src/aplicacion/parser_consulta_pricing.py",
        ROOT / "src/aplicacion/enki_pricing_query_service.py",
        ROOT / "src/api/main.py",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    metrics, output = _run(tmp_path)
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected} == before

    cases = [json.loads(line) for line in (output / "candidate_shadow_validation_dataset_v2.jsonl").read_text(encoding="utf-8").splitlines()]
    new = [item for item in cases if item["case_id"].startswith("validation-acquisition:")]
    assert len(cases) == 11
    assert len(new) == 3
    assert {item["provider_id"] for item in new} == {"provider:bitz:b7ecf7d98fe1", "provider:jadetech:2206701adec3"}
    assert {item["source_id"] for item in new} == {"bitz_generic", "jadetech_generic"}
    assert {item["expected_condition"] for item in new} == {"EXPLICIT_INCLUDED", "EXPLICIT_EXCLUDED", "UNKNOWN"}
    assert all(item["in_candidate_scope"] for item in new)
    assert metrics["AUTO_PROMOTIONS"] == 0
    assert metrics["RUNTIME_WRITES"] == 0


def test_failed_or_blocked_acquisition_cannot_erase_history_or_bypass_plan(tmp_path):
    history = tmp_path / "raw.html"
    history.write_bytes(b"keep me")
    before = history.read_bytes()
    assert classify_snapshot(hashlib.sha256(before).hexdigest(), before) == "UNCHANGED"
    assert history.read_bytes() == before
    # The real plan has local actions only; a fetcher that would fail must never be called.
    called = []
    acquire_candidate_validation_evidence(ROOT, tmp_path / "out", candidate_id=CANDIDATE_ID, fetcher=lambda *_: called.append(True))
    assert called == []


def test_conflicts_preserved_and_no_evidence_request_after_refutation(tmp_path):
    metrics, output = _run(tmp_path)
    result = json.loads((output / "candidate_shadow_validation_results_v2.jsonl").read_text(encoding="utf-8"))
    requests = (output / "candidate_shadow_validation_evidence_requests_v2.jsonl").read_text(encoding="utf-8")
    assert metrics["CONFLICTS_PRESERVED"] is True
    assert result["promotion_authorized"] is False
    assert result["runtime_effect"] is False
    assert result["rejection_reasons"] == ["FALSE_POSITIVE"]
    assert requests == ""


def test_checked_in_artifacts_are_reproducible(tmp_path):
    _, output = _run(tmp_path)
    names = (
        "candidate_validation_gap_v1.json",
        "validation_source_candidates_v1.jsonl",
        "minimal_validation_acquisition_set_v1.json",
        "candidate_validation_acquisition_outcomes_v1.jsonl",
        "candidate_validation_reusable_evidence_v1.jsonl",
        "candidate_shadow_validation_dataset_v2.jsonl",
        "candidate_shadow_validation_results_v2.jsonl",
        "candidate_shadow_validation_summary_v2.json",
        "candidate_shadow_validation_evidence_requests_v2.jsonl",
        "candidate_validation_before_after_v1.json",
        "candidate_revision_proposals_v1.jsonl",
        "candidate_validation_acquisition_summary_v1.json",
    )
    for name in names:
        assert (output / name).read_bytes() == (ROOT / "data" / name).read_bytes()
