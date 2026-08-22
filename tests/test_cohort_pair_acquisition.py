import json

from src.infraestructura.cohort_pair_acquisition import execute_positive_pair_actions


def write_plan(path, expected):
    rows = [
        {
            "action_id": f"a:{index}", "source": f"s{index}",
            "expected_pairs_unlocked": value, "expected_cohort_unlock": value,
            "expected_independent_providers_gained": int(value > 0),
        }
        for index, value in enumerate(expected)
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_zero_value_actions_never_call_network_acquirer(tmp_path):
    plan = tmp_path / "plan.jsonl"; write_plan(plan, [0, 0])
    called = []
    metrics = execute_positive_pair_actions(
        plan, tmp_path / "outcomes.jsonl",
        acquirer=lambda actions: called.append(actions) or {"NETWORK_REQUESTS": 99},
    )
    assert called == []
    assert metrics == {
        "PLANNED_ACTIONS": 2, "EXECUTED_ACTIONS": 0,
        "SKIPPED_ZERO_VALUE_ACTIONS": 2, "NETWORK_REQUESTS": 0,
        "SOURCES_SUCCEEDED": 0, "SOURCES_FAILED": 0, "BLOCKED": 0,
    }


def test_only_positive_actions_reach_explicit_acquirer(tmp_path):
    plan = tmp_path / "plan.jsonl"; write_plan(plan, [0, 2])
    called = []
    metrics = execute_positive_pair_actions(
        plan, tmp_path / "outcomes.jsonl",
        acquirer=lambda actions: called.extend(actions) or {"NETWORK_REQUESTS": 1, "SOURCES_SUCCEEDED": 1},
    )
    assert [item["action_id"] for item in called] == ["a:1"]
    assert metrics["NETWORK_REQUESTS"] == 1
    assert metrics["SKIPPED_ZERO_VALUE_ACTIONS"] == 1
