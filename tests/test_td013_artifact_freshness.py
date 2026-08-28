from __future__ import annotations

from pathlib import Path

from src.infraestructura.artifact_lifecycle import (
    ArtifactClass,
    build_manifest,
    verify_artifact_freshness,
    write_deterministic_json,
)


def _build_fixture(tmp_path: Path):
    root = tmp_path

    generator = root / "generator.py"
    source = root / "input.json"
    output = root / "output.json"

    generator.write_text(
        "print('generator')\n",
        encoding="utf-8",
    )
    source.write_text(
        '{"value":1}\n',
        encoding="utf-8",
    )

    write_deterministic_json(
        output,
        {"result": 1},
        root=root,
    )

    return root, generator, source, output


def test_current_artifact_hashes_verify(tmp_path, monkeypatch):
    root, generator, source, output = _build_fixture(
        tmp_path
    )

    monkeypatch.setattr(
        "src.infraestructura.artifact_lifecycle.current_git_head",
        lambda _root: "fixture-commit",
    )

    manifest = build_manifest(
        root=root,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
        generator_path=generator,
        input_paths=[source],
        output_path=output,
    )

    result = verify_artifact_freshness(
        manifest,
        root=root,
    )

    assert result.current is True
    assert result.reasons == ()


def test_changed_input_is_stale(tmp_path, monkeypatch):
    root, generator, source, output = _build_fixture(
        tmp_path
    )

    monkeypatch.setattr(
        "src.infraestructura.artifact_lifecycle.current_git_head",
        lambda _root: "fixture-commit",
    )

    manifest = build_manifest(
        root=root,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
        generator_path=generator,
        input_paths=[source],
        output_path=output,
    )

    source.write_text(
        '{"value":2}\n',
        encoding="utf-8",
    )

    result = verify_artifact_freshness(
        manifest,
        root=root,
    )

    assert result.current is False
    assert "INPUT_HASH_MISMATCH" in result.reasons


def test_changed_generator_is_stale(tmp_path, monkeypatch):
    root, generator, source, output = _build_fixture(
        tmp_path
    )

    monkeypatch.setattr(
        "src.infraestructura.artifact_lifecycle.current_git_head",
        lambda _root: "fixture-commit",
    )

    manifest = build_manifest(
        root=root,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
        generator_path=generator,
        input_paths=[source],
        output_path=output,
    )

    generator.write_text(
        "print('changed')\n",
        encoding="utf-8",
    )

    result = verify_artifact_freshness(
        manifest,
        root=root,
    )

    assert result.current is False
    assert "GENERATOR_HASH_MISMATCH" in result.reasons


def test_changed_output_is_stale(tmp_path, monkeypatch):
    root, generator, source, output = _build_fixture(
        tmp_path
    )

    monkeypatch.setattr(
        "src.infraestructura.artifact_lifecycle.current_git_head",
        lambda _root: "fixture-commit",
    )

    manifest = build_manifest(
        root=root,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
        generator_path=generator,
        input_paths=[source],
        output_path=output,
    )

    output.write_text(
        '{"tampered":true}\n',
        encoding="utf-8",
    )

    result = verify_artifact_freshness(
        manifest,
        root=root,
    )

    assert result.current is False
    assert "OUTPUT_HASH_MISMATCH" in result.reasons


def test_missing_input_is_stale(tmp_path, monkeypatch):
    root, generator, source, output = _build_fixture(
        tmp_path
    )

    monkeypatch.setattr(
        "src.infraestructura.artifact_lifecycle.current_git_head",
        lambda _root: "fixture-commit",
    )

    manifest = build_manifest(
        root=root,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
        generator_path=generator,
        input_paths=[source],
        output_path=output,
    )

    source.unlink()

    result = verify_artifact_freshness(
        manifest,
        root=root,
    )

    assert result.current is False
    assert "INPUT_MISSING" in result.reasons


def test_missing_generator_is_stale(tmp_path, monkeypatch):
    root, generator, source, output = _build_fixture(
        tmp_path
    )

    monkeypatch.setattr(
        "src.infraestructura.artifact_lifecycle.current_git_head",
        lambda _root: "fixture-commit",
    )

    manifest = build_manifest(
        root=root,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
        generator_path=generator,
        input_paths=[source],
        output_path=output,
    )

    generator.unlink()

    result = verify_artifact_freshness(
        manifest,
        root=root,
    )

    assert result.current is False
    assert "GENERATOR_MISSING" in result.reasons


def test_missing_output_is_stale(tmp_path, monkeypatch):
    root, generator, source, output = _build_fixture(
        tmp_path
    )

    monkeypatch.setattr(
        "src.infraestructura.artifact_lifecycle.current_git_head",
        lambda _root: "fixture-commit",
    )

    manifest = build_manifest(
        root=root,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
        generator_path=generator,
        input_paths=[source],
        output_path=output,
    )

    output.unlink()

    result = verify_artifact_freshness(
        manifest,
        root=root,
    )

    assert result.current is False
    assert "OUTPUT_MISSING" in result.reasons
