from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Iterable


class ArtifactClass(str, Enum):
    IMMUTABLE_EVIDENCE = "IMMUTABLE_EVIDENCE"
    DETERMINISTIC_DERIVED = "DETERMINISTIC_DERIVED"
    TELEMETRY = "TELEMETRY"


@dataclass(frozen=True)
class ArtifactFreshnessResult:
    current: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactManifest:
    schema_version: str
    artifact_class: ArtifactClass
    commit_sha: str
    generator_path: str
    generator_sha256: str
    input_sha256: dict[str, str]
    output_path: str
    output_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "artifact_class": self.artifact_class.value,
            "commit_sha": self.commit_sha,
            "generator_path": self.generator_path,
            "generator_sha256": self.generator_sha256,
            "input_sha256": dict(sorted(self.input_sha256.items())),
            "output_path": self.output_path,
            "output_sha256": self.output_sha256,
        }


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def current_git_head(root: str | Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(root),
        text=True,
        encoding="utf-8",
    ).strip()


def canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def canonical_json_pretty_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def is_human_real_append_only(path: str | Path, *, root: str | Path) -> bool:
    root_path = Path(root).resolve()
    target = Path(path).resolve()
    try:
        relative = target.relative_to(root_path).as_posix()
    except ValueError:
        return False
    return (
        relative.startswith("data/field/human_real_")
        and relative.endswith(".jsonl")
    )


def assert_mutation_allowed(
    path: str | Path,
    *,
    root: str | Path,
    artifact_class: ArtifactClass,
) -> None:
    if is_human_real_append_only(path, root=root):
        raise ValueError(
            "HUMAN_REAL append-only evidence cannot be rewritten by artifact lifecycle writers."
        )
    if artifact_class is ArtifactClass.IMMUTABLE_EVIDENCE:
        raise ValueError(
            "Immutable evidence cannot be written through a regenerable artifact writer."
        )


def write_deterministic_json(
    path: str | Path,
    payload: object,
    *,
    root: str | Path,
    pretty: bool = True,
) -> str:
    assert_mutation_allowed(
        path,
        root=root,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
    )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_pretty_bytes(payload) if pretty else canonical_json_bytes(payload)
    target.write_bytes(data)
    return sha256_bytes(data)


def input_hashes(
    paths: Iterable[str | Path],
    *,
    root: str | Path,
) -> dict[str, str]:
    root_path = Path(root).resolve()
    result: dict[str, str] = {}
    for item in sorted((Path(p).resolve() for p in paths), key=lambda p: p.as_posix()):
        relative = item.relative_to(root_path).as_posix()
        result[relative] = sha256_file(item)
    return result


def build_manifest(
    *,
    root: str | Path,
    artifact_class: ArtifactClass,
    generator_path: str | Path,
    input_paths: Iterable[str | Path],
    output_path: str | Path,
) -> ArtifactManifest:
    root_path = Path(root).resolve()
    generator = Path(generator_path).resolve()
    output = Path(output_path).resolve()
    # Destination directories are operational context, not artifact identity.
    # Manifests use the logical artifact filename so clean replays in different
    # temp/output directories remain byte-identical.
    output_label = output.name
    return ArtifactManifest(
        schema_version="artifact-lifecycle-manifest-v1",
        artifact_class=artifact_class,
        commit_sha=current_git_head(root_path),
        generator_path=generator.relative_to(root_path).as_posix(),
        generator_sha256=sha256_file(generator),
        input_sha256=input_hashes(input_paths, root=root_path),
        output_path=output_label,
        output_sha256=sha256_file(output),
    )


def write_manifest(path: str | Path, manifest: ArtifactManifest, *, root: str | Path) -> str:
    return write_deterministic_json(path, manifest.as_dict(), root=root, pretty=True)


def verify_artifact_freshness(
    manifest: ArtifactManifest,
    *,
    root: str | Path,
) -> ArtifactFreshnessResult:
    root_path = Path(root).resolve()
    reasons: list[str] = []

    generator = (
        root_path
        / manifest.generator_path
    )

    if not generator.is_file():
        reasons.append(
            "GENERATOR_MISSING"
        )
    elif (
        sha256_file(generator)
        != manifest.generator_sha256
    ):
        reasons.append(
            "GENERATOR_HASH_MISMATCH"
        )

    for relative, expected_hash in sorted(
        manifest.input_sha256.items()
    ):
        input_path = (
            root_path
            / relative
        )

        if not input_path.is_file():
            reasons.append(
                "INPUT_MISSING"
            )
            continue

        if (
            sha256_file(input_path)
            != expected_hash
        ):
            reasons.append(
                "INPUT_HASH_MISMATCH"
            )

    output = (
        root_path
        / manifest.output_path
    )

    if not output.is_file():
        reasons.append(
            "OUTPUT_MISSING"
        )
    elif (
        sha256_file(output)
        != manifest.output_sha256
    ):
        reasons.append(
            "OUTPUT_HASH_MISMATCH"
        )

    return ArtifactFreshnessResult(
        current=not reasons,
        reasons=tuple(reasons),
    )
