import hashlib
from pathlib import Path

from src.infraestructura.offer_evidence_artifact import (
    build_offer_evidence_sidecar,
    load_offer_evidence_sidecar,
)


ROOT = Path(__file__).parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(path: Path):
    return build_offer_evidence_sidecar(
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/pricing_sources.csv",
        ROOT / "data/offer_evidence_raw_manifest_v1.csv",
        path,
    )


def test_real_inventory_is_cardinality_safe_and_reports_no_linkage_reasons(tmp_path):
    output = tmp_path / "evidence.jsonl"
    metrics = build(output)
    loaded = load_offer_evidence_sidecar(output)

    assert metrics["TOTAL_OBSERVATIONS"] == 273
    assert metrics["WITH_SOURCE_URL"] == 273
    assert metrics["WITH_RAW_DOCUMENT"] == 98
    assert metrics["WITH_TRACEABLE_RAW"] == 78
    assert metrics["WITHOUT_TRACEABLE_RAW"] == 195
    assert metrics["RAW_DOCUMENTS_USED"] == 4
    assert metrics["NETWORK_REACQUIRE_COUNT"] == 0
    assert metrics["LINEAGE_COVERAGE"] == 0.285714
    assert metrics["RAW_LINKAGE_YIELD"] == 0.795918
    assert metrics["EXTRACTION_YIELD"] == 0.102564
    assert metrics["CLAIMS_BY_DIMENSION"]["hardware_included"] == 1
    assert metrics["NO_LINKAGE_REASONS"] == {
        "OBSERVATION_NOT_REPRODUCED_FROM_SNAPSHOT": 20,
        "SOURCE_RAW_NOT_AVAILABLE": 175,
    }
    assert len(loaded) == 273
    assert loaded["2"].lineage.linkage_status == "UNKNOWN"
    assert loaded["2"].claims == ()
    assert loaded["1"].lineage.linkage_status == "TRACEABLE_RAW"
    assert loaded["12"].lineage.linkage_status == "TRACEABLE_RAW"


def test_sidecar_is_deterministic_and_inputs_remain_unchanged(tmp_path):
    normalization = ROOT / "data/semantic_normalization_v4.csv"
    raw_paths = [
        ROOT / row
        for row in (
            "tests/fixtures/jadetech_servicio_tecnico.html",
            "tests/fixtures/bitz_tarifas_servicio_tecnico.html",
            "tests/fixtures/bairescloud.html",
            "tests/fixtures/dmr_mantenimiento.html",
        )
    ]
    before = {path: digest(path) for path in [normalization, *raw_paths]}
    one = tmp_path / "one.jsonl"
    two = tmp_path / "two.jsonl"
    build(one)
    build(two)
    assert one.read_bytes() == two.read_bytes()
    assert one.with_suffix(".summary.json").read_bytes() == two.with_suffix(".summary.json").read_bytes()
    assert before == {path: digest(path) for path in before}


def test_raw_basis_and_document_hash_are_present_for_every_claim(tmp_path):
    output = tmp_path / "evidence.jsonl"
    build(output)
    loaded = load_offer_evidence_sidecar(output)
    claims = [claim for item in loaded.values() for claim in item.claims]
    assert claims
    assert all(claim.raw_basis for claim in claims)
    assert all(claim.raw_document_id.startswith("sha256:") for claim in claims)
