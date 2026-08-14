from __future__ import annotations
import json
from pathlib import Path
CORPUS=Path("data/language/real_query_corpus_v1.jsonl")
VALID_PROVENANCE={"OBSERVED_USER","OBSERVED_REAL","RESEARCH_CANDIDATE","CURATED_ENKI","SYNTHETIC_GEMINI","SYNTHETIC_GROK","SYNTHETIC_DEEPSEEK"}
VALID_BEHAVIOR={"PARSE","CLARIFICATION","SAFE_UNSUPPORTED"}
def rows():
    return [json.loads(x) for x in CORPUS.read_text(encoding="utf-8").splitlines() if x.strip()]
def test_real_query_corpus_v1_has_50_unique_cases():
    r=rows(); assert len(r)==50; assert len({x["id"] for x in r})==50
def test_real_query_corpus_v1_provenance_is_explicit():
    for x in rows():
        assert x["provenance"] in VALID_PROVENANCE
        assert "provenance_status" in x
        if x["provenance"]=="OBSERVED_REAL": assert x["source_url"]
def test_real_query_corpus_v1_has_adjudication_contract():
    for x in rows():
        a=x["adjudication"]; assert a["expected_behavior"] in VALID_BEHAVIOR; assert isinstance(a["expected_fields"],dict); assert isinstance(a["allow_decision"],bool)
def test_real_query_corpus_v1_never_promotes_synthetic_to_observed():
    for x in rows():
        if x["provenance"].startswith("SYNTHETIC_"):
            assert x["source_url"] is None
            assert x["provenance_status"]=="ADJUDICATED_SYNTHETIC"
