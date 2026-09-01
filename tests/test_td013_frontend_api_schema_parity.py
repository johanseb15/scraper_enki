import json
from pathlib import Path

from src.api.decision_pricing_contract import (
    DecisionPricingResponse,
)


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SCHEMA = (
    ROOT
    / "frontend"
    / "src"
    / "features"
    / "decision"
    / "decision-pricing.schema.json"
)


def test_frontend_decision_schema_matches_backend_contract():
    frontend_schema = json.loads(
        FRONTEND_SCHEMA.read_text(
            encoding="utf-8",
        )
    )

    backend_schema = (
        DecisionPricingResponse.model_json_schema()
    )

    assert frontend_schema == backend_schema


def test_frontend_schema_contains_current_boundary_fields():
    schema = json.loads(
        FRONTEND_SCHEMA.read_text(
            encoding="utf-8",
        )
    )

    required = set(
        schema["required"]
    )

    assert {
        "market_resolution",
        "pricing_readiness",
        "evidence_probe",
        "parsed",
        "evidence",
    } <= required

    definitions = schema["$defs"]

    parsed = definitions[
        "DecisionPricingParsedResponse"
    ]

    assert {
        "query_kind",
        "commercial_context",
        "technical_need",
        "monetary_components",
    } <= set(parsed["required"])

    evidence = definitions[
        "DecisionPricingEvidenceResponse"
    ]

    assert {
        "source_count",
        "provider_independence_version",
        "commercial_context_provenance",
        "evidence_commercial_context",
        "temporal_state",
        "observation_ids",
    } <= set(evidence["required"])
