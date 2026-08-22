import hashlib
import json
from pathlib import Path

from src.infraestructura.targeted_claims_artifact import build_targeted_claims


ROOT = Path(__file__).parents[1]


def build(tmp_path, manifest=None):
    outputs = [tmp_path / name for name in ("claims.jsonl", "identities.jsonl", "outcomes.jsonl", "rejected.jsonl")]
    metrics = build_targeted_claims(
        ROOT / "data/semantic_normalization_v4.csv",
        ROOT / "data/pricing_sources.csv",
        ROOT / "data/evidence_acquisition_plan_v1.jsonl",
        manifest or ROOT / "data/targeted_acquisition_manifest_v1.jsonl",
        *outputs,
    )
    return metrics, [[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] for path in outputs]


def test_real_acquisition_resolves_exact_offer_identity_and_only_attributable_claim(tmp_path):
    metrics, (claims, identities, outcomes, rejected) = build(tmp_path)
    assert metrics == {
        "TARGETS": 5,
        "OFFER_IDENTITIES_RESOLVED": 5,
        "OFFER_IDENTITIES_UNRESOLVED": 0,
        "CLAIMS_EXTRACTED": 1,
        "AMBIGUOUS_APPLICABILITY_REJECTED": 1,
        "TEMPORAL_MISMATCHES": 0,
    }
    assert {(item["observation_id"], item["dimension"], item["value"]) for item in claims} == {
        ("234", "geographic_reach", "NAMED_AREA:Córdoba")
    }
    claim = claims[0]
    assert claim["raw_basis"] == "Servicio Técnico de PC / Notebooks a Domicilio en Córdoba"
    assert claim["raw_document_id"].startswith("sha256:")
    assert claim["source_url"] == "https://red-matica.com/"
    assert claim["temporal_status"] == "COMPATIBLE_EXACT_OFFER_IDENTITY"
    assert all(item["status"] == "RESOLVED" and item["offer_key"] for item in identities)
    assert sum(item["status"] == "EVIDENCE_FOUND" for item in outcomes) == 1
    assert rejected[0]["reason"] == "AMBIGUOUS_APPLICABILITY"


def test_current_scope_is_rejected_when_exact_historical_offer_cannot_be_resolved(tmp_path):
    current = [json.loads(line) for line in (ROOT / "data/targeted_acquisition_manifest_v1.jsonl").read_text(encoding="utf-8").splitlines()]
    replacement = tmp_path / "changed.html"
    replacement.write_text("<html><p>Servicio técnico a domicilio en todo el país</p></html>", encoding="utf-8")
    digest = hashlib.sha256(replacement.read_bytes()).hexdigest()
    for item in current:
        if item["source"] == "bairescloud_generic":
            item["raw_document_reference"] = str(replacement)
            item["content_hash"] = digest
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("".join(json.dumps(item) + "\n" for item in current), encoding="utf-8")

    metrics, (claims, identities, outcomes, _) = build(tmp_path, manifest)
    assert metrics["OFFER_IDENTITIES_UNRESOLVED"] == 4
    assert metrics["TEMPORAL_MISMATCHES"] == 8
    assert all(item["observation_id"] != "62" for item in claims)
    assert all(item["status"] == "TEMPORAL_MISMATCH" for item in outcomes if item["source"] == "bairescloud_generic")
    assert all(item["reason"] == "TEMPORAL_MISMATCH_OR_OFFER_NOT_FOUND" for item in identities if item["source"] == "bairescloud_generic")


def test_targeted_extraction_never_mutates_historical_inputs(tmp_path):
    normalization = ROOT / "data/semantic_normalization_v4.csv"
    historical = ROOT / "tests/fixtures/bairescloud.html"
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (normalization, historical)}
    build(tmp_path)
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before} == before
