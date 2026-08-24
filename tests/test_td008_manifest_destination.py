from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.infraestructura.real_world_trace_artifact import build_real_world_trace_artifacts

ROOT = Path(__file__).resolve().parents[1]


def test_real_world_builder_emits_reproducibility_manifests(tmp_path):
    build_real_world_trace_artifacts(ROOT, tmp_path)
    deterministic = json.loads((tmp_path / "real_world_artifact_manifest_v1.json").read_text(encoding="utf-8"))
    telemetry = json.loads((tmp_path / "real_world_telemetry_manifest_v1.json").read_text(encoding="utf-8"))

    assert deterministic["schema_version"] == "real-world-artifact-manifest-v1"
    assert telemetry["schema_version"] == "real-world-telemetry-manifest-v1"
    assert len(deterministic["artifacts"]) == 3
    assert len(telemetry["artifacts"]) == 2
    assert all(item["artifact_class"] == "DETERMINISTIC_DERIVED" for item in deterministic["artifacts"])
    assert all(item["artifact_class"] == "TELEMETRY" for item in telemetry["artifacts"])
    for manifest in deterministic["artifacts"] + telemetry["artifacts"]:
        assert len(manifest["commit_sha"]) == 40
        assert manifest["generator_sha256"].startswith("sha256:")
        assert manifest["output_sha256"].startswith("sha256:")
        assert manifest["input_sha256"]


def test_deterministic_manifest_is_identical_for_two_clean_replays(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    build_real_world_trace_artifacts(ROOT, first)
    build_real_world_trace_artifacts(ROOT, second)
    assert (first / "real_world_artifact_manifest_v1.json").read_bytes() == (second / "real_world_artifact_manifest_v1.json").read_bytes()


def test_trace_cli_requires_explicit_destination():
    process = subprocess.run(
        [str(ROOT / ".venv/Scripts/python.exe"), str(ROOT / "scripts/trace_real_world_queries.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert process.returncode != 0
    assert "--out-dir" in process.stderr


def test_trace_cli_writes_only_to_explicit_destination(tmp_path):
    process = subprocess.run(
        [str(ROOT / ".venv/Scripts/python.exe"), str(ROOT / "scripts/trace_real_world_queries.py"), "--out-dir", str(tmp_path)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert process.returncode == 0, process.stderr
    assert (tmp_path / "real_world_query_traces_v1.jsonl").exists()
    assert (tmp_path / "real_world_artifact_manifest_v1.json").exists()
    assert (tmp_path / "real_world_query_trace_telemetry_v1.jsonl").exists()
    assert (tmp_path / "real_world_telemetry_manifest_v1.json").exists()
