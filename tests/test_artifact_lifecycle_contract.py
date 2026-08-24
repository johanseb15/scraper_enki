from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.infraestructura.artifact_lifecycle import (
    ArtifactClass,
    build_manifest,
    canonical_json_bytes,
    input_hashes,
    is_human_real_append_only,
    sha256_file,
    write_deterministic_json,
)


ROOT = Path(__file__).resolve().parents[1]


def test_fixed_payload_writes_byte_identically_across_clean_runs(tmp_path):
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    payload = {"z": [3, 2, 1], "a": {"ñ": True, "x": 1}}

    first_hash = write_deterministic_json(first, payload, root=ROOT)
    second_hash = write_deterministic_json(second, payload, root=ROOT)

    assert first.read_bytes() == second.read_bytes()
    assert first_hash == second_hash == sha256_file(first)


def test_canonical_json_is_order_independent():
    left = canonical_json_bytes({"b": 2, "a": 1})
    right = canonical_json_bytes({"a": 1, "b": 2})
    assert left == right


def test_human_real_paths_are_explicitly_append_only():
    case_path = ROOT / "data/field/human_real_cases_v1.jsonl"
    trace_path = ROOT / "data/field/human_real_query_traces_v1.jsonl"
    assert is_human_real_append_only(case_path, root=ROOT)
    assert is_human_real_append_only(trace_path, root=ROOT)


def test_regenerable_writer_rejects_human_real_evidence():
    target = ROOT / "data/field/human_real_cases_v1.jsonl"
    with pytest.raises(ValueError, match="append-only evidence"):
        write_deterministic_json(target, {"forbidden": True}, root=ROOT)


def test_manifest_contains_commit_input_generator_and_output_hashes(tmp_path):
    generator = ROOT / "src/infraestructura/artifact_lifecycle.py"
    source = ROOT / "data/language/real_query_corpus_v1.jsonl"
    output = tmp_path / "derived.json"
    write_deterministic_json(output, {"derived": 1}, root=ROOT)

    # build_manifest requires repository-relative output paths by contract.
    repo_output = ROOT / ".pytest_artifact_lifecycle_manifest_probe.json"
    try:
        write_deterministic_json(repo_output, {"derived": 1}, root=ROOT)
        manifest = build_manifest(
            root=ROOT,
            artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
            generator_path=generator,
            input_paths=(source,),
            output_path=repo_output,
        )
        payload = manifest.as_dict()
        assert payload["schema_version"] == "artifact-lifecycle-manifest-v1"
        assert payload["artifact_class"] == "DETERMINISTIC_DERIVED"
        assert len(payload["commit_sha"]) == 40
        assert payload["generator_path"] == "src/infraestructura/artifact_lifecycle.py"
        assert payload["generator_sha256"].startswith("sha256:")
        assert payload["input_sha256"]["data/language/real_query_corpus_v1.jsonl"].startswith("sha256:")
        assert payload["output_path"] == ".pytest_artifact_lifecycle_manifest_probe.json"
        assert payload["output_sha256"] == sha256_file(repo_output)
    finally:
        repo_output.unlink(missing_ok=True)


def test_input_hashes_are_path_sorted_and_content_addressed():
    paths = (
        ROOT / "data/language/real_query_corpus_v1.jsonl",
        ROOT / "data/language/golden_corpus_v1.jsonl",
    )
    hashes = input_hashes(paths, root=ROOT)
    assert list(hashes) == sorted(hashes)
    assert all(value.startswith("sha256:") for value in hashes.values())
