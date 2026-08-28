from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _has_dunder_main(source: str) -> bool:
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue

        test = node.test

        if not isinstance(test, ast.Compare):
            continue

        if not (
            isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
        ):
            continue

        for comparator in test.comparators:
            if (
                isinstance(comparator, ast.Constant)
                and comparator.value == "__main__"
            ):
                return True

    return False


def _argparse_cli_scripts() -> list[Path]:
    result = []

    for path in sorted(SCRIPTS.glob("*.py")):
        source = path.read_text(
            encoding="utf-8-sig",
        )

        if not _has_dunder_main(source):
            continue

        if (
            "ArgumentParser" in source
            or "argparse." in source
        ):
            result.append(path)

    return result


ARGPARSE_CLI_SCRIPTS = _argparse_cli_scripts()


def test_td013_cli_matrix_is_not_trivially_small():
    # TD-005 established a repository-wide CLI surface.
    # This protects the boundary matrix from silently shrinking
    # to one or two hand-selected scripts.
    assert len(ARGPARSE_CLI_SCRIPTS) >= 40


@pytest.mark.parametrize(
    "script_path",
    ARGPARSE_CLI_SCRIPTS,
    ids=lambda path: path.name,
)
def test_argparse_cli_help_runs_as_real_process_without_pythonpath(
    script_path: Path,
):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path.relative_to(ROOT)),
            "--help",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        timeout=30,
    )

    stdout = completed.stdout.decode(
        "utf-8",
        errors="replace",
    )
    stderr = completed.stderr.decode(
        "utf-8",
        errors="replace",
    )

    assert completed.returncode == 0, (
        f"{script_path.name}\n"
        f"STDOUT:\n{stdout}\n"
        f"STDERR:\n{stderr}"
    )



NON_ARGPARSE_ENTRYPOINT_CLASSIFICATION = {
    "estado_repo.py": "SAFE_PROCESS_PROBE",
    "guardar_compragamer_sqlite.py": "SIDE_EFFECTFUL",
    "ingestar_todo.py": "SIDE_EFFECTFUL",
    "probar_compragamer.py": "SIDE_EFFECTFUL",
}


def _non_argparse_cli_scripts() -> list[Path]:
    result = []

    for path in sorted(SCRIPTS.glob("*.py")):
        source = path.read_text(
            encoding="utf-8-sig",
        )

        if not _has_dunder_main(source):
            continue

        if not (
            "ArgumentParser" in source
            or "argparse." in source
        ):
            result.append(path)

    return result


def test_non_argparse_entrypoints_are_explicitly_classified():
    discovered = {
        path.name
        for path in _non_argparse_cli_scripts()
    }

    assert discovered == set(
        NON_ARGPARSE_ENTRYPOINT_CLASSIFICATION
    )


def test_safe_non_argparse_entrypoint_runs_without_pythonpath():
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/estado_repo.py",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        timeout=30,
    )

    stdout = completed.stdout.decode(
        "utf-8",
        errors="replace",
    )
    stderr = completed.stderr.decode(
        "utf-8",
        errors="replace",
    )

    assert completed.returncode == 0, (
        f"STDOUT:\n{stdout}\n"
        f"STDERR:\n{stderr}"
    )
