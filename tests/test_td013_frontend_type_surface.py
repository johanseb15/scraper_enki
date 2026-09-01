from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TYPES = (
    ROOT
    / "frontend"
    / "src"
    / "features"
    / "decision"
    / "types.ts"
)


def test_frontend_decision_types_cover_backend_boundary_fields():
    text = TYPES.read_text(
        encoding="utf-8",
    )

    required_tokens = {
        "query_kind:",
        "commercial_context:",
        "technical_need:",
        "monetary_components:",
        "market_resolution:",
        "pricing_readiness:",
        "evidence_probe:",
        "source_count:",
        "provider_independence_version:",
        "commercial_context_provenance:",
        "evidence_commercial_context:",
        "temporal_state:",
        "observation_ids:",
    }

    missing = sorted(
        token
        for token in required_tokens
        if token not in text
    )

    assert not missing, missing
