from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

README = ROOT / "README.md"
PROJECT_STATUS = ROOT / "docs/PROJECT_STATUS.md"
MANIFESTO = ROOT / "docs/ENKI_ENGINEERING_MANIFESTO.md"
RECTOR = ROOT / "docs/ENKI_ARCHIVO_RECTOR.md"
DEBT_REGISTER = ROOT / "docs/TECHNICAL_DEBT_REGISTER.md"
GITIGNORE = ROOT / ".gitignore"


def _read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
    )


def test_rector_is_the_only_current_governance_authority():
    assert RECTOR.exists()

    status = _read(PROJECT_STATUS)
    manifesto = _read(MANIFESTO)

    assert "docs/ENKI_ARCHIVO_RECTOR.md" in status
    assert "docs/ENKI_ARCHIVO_RECTOR.md" in manifesto

    assert "README.md sigue siendo la fuente" not in status

    assert (
        "README.md define la orientacion estrategica superior"
        not in manifesto
    )


def test_project_status_is_explicitly_historical():
    text = _read(PROJECT_STATUS)

    assert "HISTORICAL SNAPSHOT" in text
    assert "estado operativo actual" not in text.lower()


def test_readme_old_sprint_roadmap_is_explicitly_historical():
    text = _read(README)

    assert "HISTORICAL" in text

    assert "## 14. Recuper" not in text
    assert "## 15. Qu" not in text


def test_engineering_manifesto_does_not_override_program_sequence():
    text = _read(MANIFESTO)

    assert "ENTENDER" in text
    assert "CONECTAR" in text
    assert "APRENDER" in text
    assert "EXPLOTAR ECONOMICAMENTE" in text

    assert (
        "El cuello de botella actual es **Economic Evidence Acquisition**"
        not in text
    )


def test_pytest_temp_outputs_are_ignored():
    text = _read(GITIGNORE)

    assert ".pytest_tmp/" in text
    assert ".pytest_tmp_*/" in text


def test_technical_debt_headings_have_no_encoding_residue():
    text = _read(DEBT_REGISTER)

    assert "### TD-012 -" not in text
    assert "### TD-013 ?" not in text
