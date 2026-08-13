from __future__ import annotations
import json
from pathlib import Path
import pytest
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

CORPUS = Path("data/language/golden_corpus_v1.jsonl")

def _cases():
    return [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]

def _actual(r):
    return {
        "intent_action": r.intent_action.value,
        "intent_side": r.intent_side.value,
        "economic_object_kind": r.economic_object_kind.value,
        "canonical_services": list(r.canonical_services),
        "market_scope": r.market_scope.value,
        "modality": r.modality.value,
        "price": {
            "type": r.price.type.value,
            "value": r.price.value,
            "min": r.price.min,
            "max": r.price.max,
            "currency": r.price.currency,
            "is_approximate": r.price.is_approximate,
        },
        "geography": {
            "province": r.geography.province,
            "city": r.geography.city,
        },
        "device_type": r.device_type,
        "condition": r.condition,
        "is_bundle": r.is_bundle,
        "parts_scope": r.commercial_context.parts_scope.value,
        "clarification_required": r.metadata.clarification_required,
        "clarification_reason": r.metadata.clarification_reason,
    }

@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["id"])
def test_golden_language_corpus(case):
    result = parse_pricing_query(
        case["query_raw"],
        language_evidence_type=case["language_evidence_type"],
    )
    assert result.language_evidence_type == case["language_evidence_type"]
    assert _actual(result) == case["expect"]
