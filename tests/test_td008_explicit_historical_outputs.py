from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# HUMAN_REAL appenders intentionally keep stable append-only defaults.
EXEMPT_APPEND_ONLY = {
    "append_founder_feedback.py",
    "trace_real_query.py",
}

# Read-only input defaults are not output ownership.
READ_ONLY_FLAGS = {
    "--corpus",
    "--review",
    "--normalization",
    "--sources",
    "--baseline",
    "--local-stats",
    "--remote-stats",
}

MUTATING_ENTRYPOINTS = {
    "acquire_candidate_validation_evidence.py",
    "audit_real_query_corpus.py",
    "build_commercial_context_single_truth.py",
    "build_knowledge_candidates.py",
    "build_offer_service_reach_admission_gate.py",
    "build_pricing_statistics.py",
    "build_runtime_cohort_lineage_gate.py",
    "build_semantic_normalization_live.py",
    "build_temporal_evidence_admissibility.py",
    "reconcile_price_scope_contract.py",
    "run_candidate_shadow_validation.py",
    "trace_real_world_queries.py",
}


def _argparse_calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        attr = node.func
        if not isinstance(attr, ast.Attribute) or attr.attr != "add_argument":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        flag = node.args[0].value
        kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
        yield flag, kwargs


def _literal(node):
    return node.value if isinstance(node, ast.Constant) else None


def test_mutating_historical_entrypoints_do_not_default_outputs_into_data():
    scripts = ROOT / "scripts"
    for name in sorted(MUTATING_ENTRYPOINTS):
        path = scripts / name
        assert path.exists(), name
        if name in EXEMPT_APPEND_ONLY:
            continue
        for flag, kwargs in _argparse_calls(path):
            if flag in READ_ONLY_FLAGS:
                continue
            default = _literal(kwargs.get("default"))
            if isinstance(default, str) and default.replace("\\", "/").startswith("data/"):
                raise AssertionError(f"{name} {flag} still defaults output to tracked data path: {default}")


def test_known_historical_generators_require_explicit_output_destination():
    scripts = ROOT / "scripts"
    required_flags = {
        "acquire_candidate_validation_evidence.py": {"--out-dir"},
        "audit_real_query_corpus.py": {"--out"},
        "build_commercial_context_single_truth.py": {"--out"},
        "build_knowledge_candidates.py": {"--out-dir"},
        "build_offer_service_reach_admission_gate.py": {"--out", "--local-out", "--remote-out"},
        "build_pricing_statistics.py": {"--local-out", "--remote-out"},
        "build_runtime_cohort_lineage_gate.py": {"--out", "--local-out", "--remote-out"},
        "build_semantic_normalization_live.py": {"--out"},
        "build_temporal_evidence_admissibility.py": {"--out", "--temporal-out", "--local-out", "--remote-out"},
        "reconcile_price_scope_contract.py": {"--out-dir"},
        "run_candidate_shadow_validation.py": {"--out-dir"},
        "trace_real_world_queries.py": {"--out-dir"},
    }
    for name, expected in required_flags.items():
        calls = {flag: kwargs for flag, kwargs in _argparse_calls(scripts / name)}
        for flag in expected:
            assert flag in calls, (name, flag)
            assert _literal(calls[flag].get("required")) is True, (name, flag)


def test_human_real_append_only_cli_defaults_are_preserved():
    scripts = ROOT / "scripts"
    trace = dict(_argparse_calls(scripts / "trace_real_query.py"))
    assert _literal(trace["--out"]["default"]) == "data/field/human_real_query_traces_v1.jsonl"
    assert _literal(trace["--cases-out"]["default"]) == "data/field/human_real_cases_v1.jsonl"
