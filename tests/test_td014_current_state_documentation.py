from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ARCHITECTURE = ROOT / "ARCHITECTURE.md"
RECTOR = ROOT / "docs/ENKI_ARCHIVO_RECTOR.md"


def _read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
    )


def test_readme_uses_verifiable_current_state_commands():
    text = _read(README)

    assert "git rev-parse HEAD" in text
    assert "python -m pytest -q" in text

    assert "HEAD: 40624fd" not in text
    assert "backend: 252 tests GREEN" not in text
    assert "frontend: 9 tests GREEN" not in text


def test_documentation_declares_rector_as_governance_authority():
    readme = _read(README)
    architecture = _read(ARCHITECTURE)

    assert "docs/ENKI_ARCHIVO_RECTOR.md" in readme
    assert "docs/ENKI_ARCHIVO_RECTOR.md" in architecture

    assert "fuente de orientaci?n estrat?gica de mayor nivel" not in architecture


def test_architecture_describes_current_decision_runtime():
    text = _read(ARCHITECTURE)

    assert "/decision/pricing" in text
    assert "DecisionPricingResponse" in text
    assert "pricing engine completo" not in text.lower()


def test_readme_does_not_override_current_program_sequence():
    text = _read(README)

    assert "ENTENDER" in text
    assert "CONECTAR" in text
    assert "APRENDER" in text
    assert "EXPLOTAR ECONÓMICAMENTE" in text
