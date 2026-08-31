import json
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PYTEST_INI = ROOT / "pytest.ini"
FRONTEND_PACKAGE = ROOT / "frontend" / "package.json"


def _pyproject() -> dict:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


def test_pyproject_is_the_single_pytest_configuration_authority():
    config = _pyproject()

    pytest_config = config["tool"]["pytest"]["ini_options"]

    assert pytest_config["testpaths"] == ["tests"]
    assert pytest_config["pythonpath"] == [".", "src"]
    assert pytest_config["addopts"] == "-v"

    assert not PYTEST_INI.exists()
    assert "coverage" not in config.get("tool", {})


def test_backend_has_explicit_package_metadata():
    config = _pyproject()

    assert "build-system" in config
    assert "project" in config

    build_system = config["build-system"]
    project = config["project"]

    assert build_system["build-backend"] == "setuptools.build_meta"
    assert project["name"] == "enki"
    assert project["requires-python"] == ">=3.14"


def test_frontend_package_declares_esm_for_vitest_config():
    package = json.loads(FRONTEND_PACKAGE.read_text(encoding="utf-8"))

    assert package["type"] == "module"
