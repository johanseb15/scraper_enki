from pathlib import Path

from src.dominio.economic_evidence import DimensionStatus
from src.dominio.offer_evidence import SourceClaimMethod, SourceEconomicClaim
from src.infraestructura.economic_dimensions_v2_adapter import (
    derive_economic_dimensions_v2,
)
from src.infraestructura.economic_dimensions_v2_artifact import (
    build_economic_dimensions_v2_sidecar,
    load_economic_dimensions_v2_sidecar,
)
from src.infraestructura.offer_evidence_artifact import build_offer_evidence_sidecar


ROOT = Path(__file__).parents[1]


def claim(dimension: str, value: str) -> SourceEconomicClaim:
    return SourceEconomicClaim(
        observation_id="1",
        dimension=dimension,
        value=value,
        raw_basis=f"explicit {value}",
        raw_document_id="sha256:abc",
        extraction_method=SourceClaimMethod.SOURCE_TEXT_EXPLICIT,
        provenance="raw.html",
    )


def test_source_charged_unit_and_reach_feed_v2_without_overwriting_claims():
    row = {"observation_id": "1", "source": "x", "currency": "ARS"}
    dimensions = derive_economic_dimensions_v2(
        row,
        {},
        (claim("charged_unit", "VISIT"), claim("geographic_reach", "NATIONAL")),
    )
    assert dimensions.price_scope.value == "PER_VISIT"
    assert dimensions.geographic_reach.value == "NATIONAL"
    assert dimensions.price_scope.status is DimensionStatus.OBSERVED
    assert dimensions.price_scope.claims[0].raw_basis == "explicit VISIT"


def test_contradictory_source_claims_remain_ambiguous():
    dimensions = derive_economic_dimensions_v2(
        {"observation_id": "1", "source": "x"},
        {},
        (claim("geographic_reach", "NATIONAL"), claim("geographic_reach", "CITY:Córdoba")),
    )
    assert dimensions.geographic_reach.status is DimensionStatus.AMBIGUOUS
    assert {item.value for item in dimensions.geographic_reach.claims} == {
        "NATIONAL", "CITY:Córdoba"
    }


def test_real_enrichment_preserves_currency_conflicts_and_cardinality(tmp_path):
    offer = tmp_path / "offer.jsonl"
    dimensions = tmp_path / "dimensions.jsonl"
    build_offer_evidence_sidecar(
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/pricing_sources.csv",
        ROOT / "data/offer_evidence_raw_manifest_v1.csv",
        offer,
    )
    metrics = build_economic_dimensions_v2_sidecar(
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/pricing_sources.csv",
        dimensions,
        previous_dimensions_path=ROOT / "data/economic_dimensions_v1.jsonl",
        offer_evidence_path=offer,
    )
    loaded = load_economic_dimensions_v2_sidecar(dimensions)
    assert len(loaded) == 273
    assert metrics["SOURCE_EXPLICIT_REACH"] == 0
    assert metrics["SOURCE_EXPLICIT_SCOPE"] == 4
    assert loaded["62"].price_scope.value == "PER_UNIT"
    assert metrics["SOURCE_EXPLICIT_DELIVERY_MODE"] == 7
    assert metrics["CONFLICTED_DIMENSIONS"] == {"currency": 3}
    assert all(loaded[value].currency.status is DimensionStatus.CONFLICTED for value in ("159", "160", "161"))
