from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.infraestructura.offer_observation_projection_artifact import (
    build_offer_observation_projection_bundle,
)

ROOT = Path(__file__).resolve().parents[1]


def test_real_projection_bundle_emits_artifact_and_lifecycle_manifest(tmp_path):
    metrics = build_offer_observation_projection_bundle(
        root=ROOT,
        output_dir=tmp_path,
    )

    artifact = tmp_path / "offer_observations_v1.jsonl"
    manifest_path = tmp_path / "offer_observations_manifest_v1.json"

    assert artifact.exists()
    assert manifest_path.exists()

    rows = [
        json.loads(line)
        for line in artifact.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(rows) == 9
    assert metrics == {
        "TOTAL_ROWS": 9,
        "RESOLVED": 5,
        "UNRESOLVED": 4,
    }

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    assert manifest["schema_version"] == "artifact-lifecycle-manifest-v1"
    assert manifest["artifact_class"] == "DETERMINISTIC_DERIVED"
    assert len(manifest["commit_sha"]) == 40

    assert (
        manifest["generator_path"]
        == "src/infraestructura/offer_observation_projection_artifact.py"
    )
    assert manifest["generator_sha256"].startswith("sha256:")

    assert manifest["output_path"] == "offer_observations_v1.jsonl"
    assert manifest["output_sha256"].startswith("sha256:")

    assert set(manifest["input_sha256"]) == {
        "data/semantic_normalization_v4.csv",
        "data/offer_evidence_identities_v1.jsonl",
        "data/offer_evidence_v1.jsonl",
        "data/economic_dimensions_v2.jsonl",
    }

    assert all(
        value.startswith("sha256:")
        for value in manifest["input_sha256"].values()
    )


def test_real_projection_bundle_is_byte_deterministic_across_destinations(
    tmp_path,
):
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_metrics = build_offer_observation_projection_bundle(
        root=ROOT,
        output_dir=first,
    )

    second_metrics = build_offer_observation_projection_bundle(
        root=ROOT,
        output_dir=second,
    )

    assert first_metrics == second_metrics

    assert (
        (first / "offer_observations_v1.jsonl").read_bytes()
        == (second / "offer_observations_v1.jsonl").read_bytes()
    )

    assert (
        (first / "offer_observations_manifest_v1.json").read_bytes()
        == (second / "offer_observations_manifest_v1.json").read_bytes()
    )


def test_projection_cli_requires_explicit_output_destination():
    process = subprocess.run(
        [
            str(ROOT / ".venv/Scripts/python.exe"),
            str(ROOT / "scripts/build_offer_observations.py"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert process.returncode != 0
    assert "--out-dir" in process.stderr


def test_projection_cli_writes_only_to_explicit_destination(tmp_path):
    process = subprocess.run(
        [
            str(ROOT / ".venv/Scripts/python.exe"),
            str(ROOT / "scripts/build_offer_observations.py"),
            "--out-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert process.returncode == 0, process.stderr

    assert (tmp_path / "offer_observations_v1.jsonl").exists()
    assert (tmp_path / "offer_observations_manifest_v1.json").exists()

    assert "TOTAL_ROWS=9" in process.stdout
    assert "RESOLVED=5" in process.stdout
    assert "UNRESOLVED=4" in process.stdout


def test_real_projection_bundle_materializes_snapshot_safe_dimensions(tmp_path):
    build_offer_observation_projection_bundle(
        root=ROOT,
        output_dir=tmp_path,
    )

    rows = [
        json.loads(line)
        for line in (tmp_path / "offer_observations_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert len(rows) == 9
    assert sum(row["status"] == "RESOLVED" for row in rows) == 5
    assert sum(row["status"] == "UNRESOLVED" for row in rows) == 4
    assert len({
        row["snapshot_observation_id"]
        for row in rows
        if row["status"] == "RESOLVED"
    }) == 5

    assert all("economic_dimensions" in row for row in rows)

    targeted_62 = next(
        row for row in rows
        if row["source_observation_id"] == "62"
        and row["raw_document_id"].startswith("sha256:f043")
    )
    historical_62 = next(
        row for row in rows
        if row["source_observation_id"] == "62"
        and row["raw_document_id"].startswith("sha256:d822")
    )

    assert targeted_62["status"] == "RESOLVED"
    assert historical_62["status"] == "UNRESOLVED"

    targeted_delivery = targeted_62["economic_dimensions"]["delivery_mode"]

    assert targeted_delivery["status"] == "UNKNOWN"
    assert all(
        "raw_document_id=sha256:f043" in claim["provenance"]["origin_reference"]
        for dimension in targeted_62["economic_dimensions"].values()
        for claim in dimension["claims"]
        if claim["origin"] == "RAW_SOURCE_OBSERVATION"
    )
    assert all(
        "raw_document_id=sha256:d822" in claim["provenance"]["origin_reference"]
        for dimension in historical_62["economic_dimensions"].values()
        for claim in dimension["claims"]
        if claim["origin"] == "RAW_SOURCE_OBSERVATION"
    )

    obs234 = next(
        row for row in rows
        if row["source_observation_id"] == "234"
    )
    assert all(
        "raw_document_id=sha256:a0d741" in claim["provenance"]["origin_reference"]
        for dimension in obs234["economic_dimensions"].values()
        for claim in dimension["claims"]
        if claim["origin"] == "RAW_SOURCE_OBSERVATION"
    )


def test_real_projection_manifest_includes_economic_dimensions_input(tmp_path):
    build_offer_observation_projection_bundle(
        root=ROOT,
        output_dir=tmp_path,
    )

    manifest = json.loads(
        (tmp_path / "offer_observations_manifest_v1.json")
        .read_text(encoding="utf-8")
    )

    assert set(manifest["input_sha256"]) == {
        "data/semantic_normalization_v4.csv",
        "data/offer_evidence_identities_v1.jsonl",
        "data/offer_evidence_v1.jsonl",
        "data/economic_dimensions_v2.jsonl",
    }
