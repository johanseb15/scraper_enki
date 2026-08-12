import json
from datetime import datetime, timezone
from pathlib import Path

from src.aplicacion.colector_precios_os_jadetech import ColectorPreciosOSJadetech
from src.infraestructura.scrapers.jadetech_os_parser import (
    extraer_observaciones_jadetech_os,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)

URL = "https://jadetech.com.ar/categoria/servicio-tecnico/"

class DownloaderFake:
    def __init__(self, html: str): self.html = html
    def descargar(self, url: str) -> str:
        assert url == URL
        return self.html

def _fixture() -> str:
    return Path("tests/fixtures/jadetech_servicio_tecnico.html").read_text(encoding="utf-8")

def _collector(repo, html, when):
    return ColectorPreciosOSJadetech(
        repositorio=repo,
        downloader=DownloaderFake(html),
        parser_observaciones=extraer_observaciones_jadetech_os,
        reloj=lambda: when,
    )

def test_parser_extrae_solo_observacion_sin_backup_y_preserva_unknowns():
    observaciones = extraer_observaciones_jadetech_os(
        _fixture(), source_url=URL, raw_document_id=1,
        retrieved_at=datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc),
    )
    assert len(observaciones) == 1
    observacion = observaciones[0]
    assert observacion.economic_object_raw == "Formateo e instalación de Sistema Operativo sin BackUp"
    assert observacion.price_raw == "$ 42.120,00"
    assert observacion.price_value == 42120
    assert observacion.currency_raw == "ARS"
    assert observacion.backup_raw == "NO"
    assert observacion.drivers_raw == "UNKNOWN"
    assert observacion.programs_raw == "UNKNOWN"
    assert observacion.license_raw == "UNKNOWN"
    assert observacion.comparable_status == "COMPARABLE_CORE"

def test_parser_rechaza_paquete_con_backup_hardware_y_programas():
    observaciones = extraer_observaciones_jadetech_os(
        _fixture(), source_url=URL, raw_document_id=1,
        retrieved_at=datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc),
    )
    assert all("BackUp hasta 100gb" not in o.economic_object_raw for o in observaciones)
    assert all("Limpieza Hardware" not in o.economic_object_raw for o in observaciones)

def test_collector_preserva_raw_extrae_observacion_y_mantiene_trazabilidad(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    collector = _collector(repo, _fixture(), datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc))
    resultado = collector.colectar()
    assert resultado.raw_docs_acquired == 1
    assert resultado.observations_extracted == 1
    assert resultado.exact_prices == 1
    assert resultado.candidate_comparable_core == 1
    documentos = repo.listar_documentos_raw(source="jadetech_os_installation")
    assert len(documentos) == 1
    assert documentos[0].source_url == URL
    assert documentos[0].raw_content == _fixture()
    assert documentos[0].metadata["provider_name"] == "Jadetech"
    observaciones = repo.listar_observaciones_precios_comerciales(extractor_version="jadetech_os_installation_v1")
    assert len(observaciones) == 1
    assert observaciones[0].raw_document_id == documentos[0].storage_id
    assert observaciones[0].source_url == documentos[0].source_url
    assert observaciones[0].metadata["content_hash"] == documentos[0].content_hash

def test_collector_es_idempotente_por_raw_y_extractor_version(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    collector = _collector(repo, _fixture(), datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc))
    collector.colectar()
    resultado = collector.colectar()
    assert resultado.raw_docs_acquired == 0
    assert resultado.raw_docs_duplicate == 1
    assert resultado.observations_extracted == 0
    assert resultado.observations_duplicate == 1
    assert repo.contar_documentos_raw(source="jadetech_os_installation") == 1
    assert repo.contar_observaciones_precios_comerciales(extractor_version="jadetech_os_installation_v1") == 1

def test_observacion_persistida_conserva_campos_raw_en_json(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    collector = _collector(repo, _fixture(), datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc))
    collector.colectar()
    observacion = repo.listar_observaciones_precios_comerciales()[0]
    assert json.loads(json.dumps(observacion.metadata))["cohort_contract"]["backup"] == "NO explícito"

def test_collector_no_duplica_observacion_si_cambia_raw_pero_no_el_precio(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    html_1 = _fixture()
    html_2 = html_1.replace("</body>", "<!-- contenido dinamico irrelevante -->\n</body>")
    collector_1 = _collector(repo, html_1, datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc))
    collector_2 = _collector(repo, html_2, datetime(2026, 8, 12, 15, 5, tzinfo=timezone.utc))
    resultado_1 = collector_1.colectar()
    resultado_2 = collector_2.colectar()
    assert resultado_1.raw_docs_acquired == 1
    assert resultado_1.observations_extracted == 1
    assert resultado_2.raw_docs_acquired == 1
    assert resultado_2.observations_extracted == 0
    assert resultado_2.observations_duplicate == 1
    assert repo.contar_documentos_raw(source="jadetech_os_installation") == 2
    assert repo.contar_observaciones_precios_comerciales(extractor_version="jadetech_os_installation_v1") == 1

def test_collector_inserta_nueva_observacion_si_cambia_el_precio(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    html_1 = _fixture()
    html_2 = html_1.replace("$ 42.120,00", "$ 45.000,00")
    collector_1 = _collector(repo, html_1, datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc))
    collector_2 = _collector(repo, html_2, datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc))
    resultado_1 = collector_1.colectar()
    resultado_2 = collector_2.colectar()
    assert resultado_1.observations_extracted == 1
    assert resultado_2.observations_extracted == 1
    assert resultado_2.observations_duplicate == 0
    observaciones = repo.listar_observaciones_precios_comerciales(extractor_version="jadetech_os_installation_v1")
    assert len(observaciones) == 2
    assert [o.price_value for o in observaciones] == [42120, 45000]
