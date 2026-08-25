from __future__ import annotations

from scripts.audit_real_query_corpus import classify


class _Parsed:
    pass


class _Result:
    def __init__(self, status):
        self.status = status
        self.parsed = _Parsed()


def _record(expected_status):
    return {
        "adjudication": {
            "expected_behavior": "PARSE",
            "expected_resolution_status": expected_status,
            "allow_decision": False,
            "expected_fields": {},
        }
    }


def test_range_to_no_evidence_is_expected_safety_change():
    outcome, errors = classify(
        _record("RANGE_READY"),
        _Result("NO_EVIDENCE"),
    )
    assert outcome == "EXPECTED_SAFETY_CHANGE"
    assert errors == []


def test_decision_to_insufficient_is_expected_safety_change():
    outcome, errors = classify(
        _record("DECISION_READY"),
        _Result("INSUFFICIENT_EVIDENCE"),
    )
    assert outcome == "EXPECTED_SAFETY_CHANGE"
    assert errors == []


def test_clarification_is_still_wrong_for_parse_path():
    outcome, errors = classify(
        _record("RANGE_READY"),
        _Result("CLARIFICATION_REQUIRED"),
    )
    assert outcome == "WRONG_INTERPRETATION"
    assert errors
