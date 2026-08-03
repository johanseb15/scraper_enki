import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOMINIO_DIR = ROOT / "src" / "dominio"
SCRAPERS_DIR = ROOT / "src" / "scrapers"
APLICACION_DIR = ROOT / "src" / "aplicacion"
INFRAESTRUCTURA_DIR = ROOT / "src" / "infraestructura"


def _iter_python_files(directory: Path):
    return sorted(directory.rglob("*.py"))


def _import_nodes(tree: ast.AST):
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
    return imports


def test_dominio_no_depende_de_infraestructura():
    dominio_files = _iter_python_files(DOMINIO_DIR)

    violations = []

    for file_path in dominio_files:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        imports = _import_nodes(tree)

        for module in imports:
            if module and module.startswith("src.infraestructura"):
                violations.append(str(file_path.relative_to(ROOT)))
                break

    assert not violations, (
        "El dominio no debe importar módulos de infraestructura: "
        f"{violations}"
    )


def test_scrapers_no_crean_entidades_de_dominio():
    scraper_files = _iter_python_files(SCRAPERS_DIR)

    violations = []

    for file_path in scraper_files:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        source = file_path.read_text(encoding="utf-8")
        if "src.dominio" in source:
            violations.append(str(file_path.relative_to(ROOT)))

    assert not violations, (
        "Los scrapers no deben crear entidades de dominio: "
        f"{violations}"
    )


def test_aplicacion_no_depende_de_sqlite_directamente():
    aplicacion_files = _iter_python_files(APLICACION_DIR)

    violations = []

    for file_path in aplicacion_files:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        imports = _import_nodes(tree)
        for module in imports:
            if module and module.startswith("src.infraestructura"):
                violations.append(str(file_path.relative_to(ROOT)))
                break

    assert not violations, (
        "La aplicación no debe depender directamente de SQLite: "
        f"{violations}"
    )


def test_pipeline_usa_ofertadto_como_contrato():
    pipeline_files = [
        ROOT / "src" / "pipeline.py",
        ROOT / "src" / "extractor.py",
        ROOT / "src" / "aplicacion" / "procesador_ofertas.py",
        ROOT / "src" / "aplicacion" / "oferta_factory.py",
        ROOT / "src" / "scrapers" / "base.py",
    ]

    violations = []

    for file_path in pipeline_files:
        source = file_path.read_text(encoding="utf-8")
        if "OfertaDTO" not in source and "oferta_dto" not in source:
            violations.append(str(file_path.relative_to(ROOT)))

    assert not violations, (
        "El pipeline debe referenciar OfertaDTO como contrato: "
        f"{violations}"
    )
