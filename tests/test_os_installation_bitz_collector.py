import json
from datetime import datetime, timezone
from pathlib import Path

from src.aplicacion.colector_precios_os_jadetech import (
    ColectorPreciosOSJadetech,
)
from src.infraestructura.scrapers.bitz_os_parser import (
    extraer_observaciones_bitz_os,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)

URL = "https://bitz.com.ar/tarifas-de-servicio-tecnico"


class DownloaderFake:
    def __init__(self, html: str):
        self.html = html

    def descargar(self, url: str) -> str:
        assert url == URL
        return self.html


def _fixture() -> str:
    return Path(
        "tests/fixtures/bitz_tarifas_servicio_tecnico.html"
    ).read_text(encoding="utf-8")


def _collector(repo, html, when):
    return ColectorPreciosOSJadetech(
        repositorio=repo,
        downloader=DownloaderFake(html),
        parser_observaciones=(
            extraer_observaciones_bitz_os
        ),
        reloj=lambda: when,
        source_url=URL,
        source="bitz_os_installation",
        provider="Bitz",
        extractor_version=(
            "bitz_os_installation_v1"
        ),
        source_notes=(
            "Bitz Formateo + Configuración "
            "commercial pricing source"
        ),
    )


def test_parser_extrae_formateo_configuracion_por_tipo_equipo():
    observaciones = extraer_observaciones_bitz_os(
        _fixture(),
        source_url=URL,
        raw_document_id=1,
        retrieved_at=datetime(
            2026, 8, 12, 19, 0, tzinfo=timezone.utc
        ),
    )

    assert len(observaciones) == 6

    observaciones_por_equipo = {
        o.device_type_raw: o
        for o in observaciones
    }

    assert observaciones_por_equipo["PC Antigua Básica"].price_value == 15000
    assert observaciones_por_equipo["PC Todas"].price_value == 35000
    assert observaciones_por_equipo["Notebook básica"].price_value == 50000
    assert observaciones_por_equipo["Notebook Gamer/Pro"].price_value == 60000
    assert observaciones_por_equipo["Notebook Ultra/Premium"].price_value == 80000
    assert observaciones_por_equipo["AIO estándar"].price_value == 50000


def test_parser_preserva_objeto_precio_y_moneda_raw():
    observaciones = extraer_observaciones_bitz_os(
        _fixture(),
        source_url=URL,
        raw_document_id=1,
        retrieved_at=datetime(
            2026, 8, 12, 19, 0, tzinfo=timezone.utc
        ),
    )

    observacion = next(
        o for o in observaciones
        if o.device_type_raw == "PC Todas"
    )

    assert observacion.economic_object_raw == "Formateo + Configuración"
    assert observacion.price_raw == "$35,000"
    assert observacion.price_value == 35000
    assert observacion.currency_raw == "ARS"


def test_parser_no_convierte_consultar_en_precio():
    observaciones = extraer_observaciones_bitz_os(
        _fixture(),
        source_url=URL,
        raw_document_id=1,
        retrieved_at=datetime(
            2026, 8, 12, 19, 0, tzinfo=timezone.utc
        ),
    )

    assert all(
        o.device_type_raw != "AIO Premium/Ultra/Apple"
        for o in observaciones
    )


def test_parser_no_inventa_scope_no_publicado():
    observaciones = extraer_observaciones_bitz_os(
        _fixture(),
        source_url=URL,
        raw_document_id=1,
        retrieved_at=datetime(
            2026, 8, 12, 19, 0, tzinfo=timezone.utc
        ),
    )

    assert len(observaciones) == 6

    for observacion in observaciones:
        assert observacion.backup_raw == "UNKNOWN"
        assert observacion.drivers_raw == "UNKNOWN"
        assert observacion.programs_raw == "UNKNOWN"
        assert observacion.license_raw == "UNKNOWN"


def test_collector_bitz_preserva_raw_y_persiste_seis_observaciones(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))

    collector = _collector(
        repo,
        _fixture(),
        datetime(2026, 8, 12, 19, 0, tzinfo=timezone.utc),
    )

    resultado = collector.colectar()

    assert resultado.raw_docs_acquired == 1
    assert resultado.observations_extracted == 6
    assert resultado.exact_prices == 6

    documentos = repo.listar_documentos_raw(
        source="bitz_os_installation"
    )

    assert len(documentos) == 1
    assert documentos[0].source_url == URL
    assert documentos[0].raw_content == _fixture()

    observaciones = repo.listar_observaciones_precios_comerciales(
        extractor_version="bitz_os_installation_v1"
    )

    assert len(observaciones) == 6

    assert {o.price_value for o in observaciones} == {
        15000,
        35000,
        50000,
        60000,
        80000,
    }


def test_collector_bitz_es_idempotente(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))

    collector = _collector(
        repo,
        _fixture(),
        datetime(2026, 8, 12, 19, 0, tzinfo=timezone.utc),
    )

    collector.colectar()
    resultado = collector.colectar()

    assert resultado.raw_docs_acquired == 0
    assert resultado.raw_docs_duplicate == 1

    assert resultado.observations_extracted == 0
    assert resultado.observations_duplicate == 6

    assert (
        repo.contar_observaciones_precios_comerciales(
            extractor_version="bitz_os_installation_v1"
        )
        == 6
    )


def test_collector_bitz_no_duplica_si_cambia_raw_pero_no_economia(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))

    html_1 = _fixture()

    html_2 = html_1.replace(
        "</body>",
        "<!-- contenido dinamico irrelevante -->\n</body>",
    )

    collector_1 = _collector(
        repo,
        html_1,
        datetime(2026, 8, 12, 19, 0, tzinfo=timezone.utc),
    )

    collector_2 = _collector(
        repo,
        html_2,
        datetime(2026, 8, 12, 19, 5, tzinfo=timezone.utc),
    )

    resultado_1 = collector_1.colectar()
    resultado_2 = collector_2.colectar()

    assert resultado_1.raw_docs_acquired == 1
    assert resultado_1.observations_extracted == 6

    assert resultado_2.raw_docs_acquired == 1
    assert resultado_2.observations_extracted == 0
    assert resultado_2.observations_duplicate == 6

    assert (
        repo.contar_documentos_raw(
            source="bitz_os_installation"
        )
        == 2
    )

    assert (
        repo.contar_observaciones_precios_comerciales(
            extractor_version="bitz_os_installation_v1"
        )
        == 6
    )


def test_collector_bitz_inserta_solo_la_observacion_cuyo_precio_cambio(
    tmp_path,
):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))

    html_1 = _fixture()

    html_2 = html_1.replace(
        "$35,000",
        "$37,000",
        1,
    )

    collector_1 = _collector(
        repo,
        html_1,
        datetime(2026, 8, 12, 19, 0, tzinfo=timezone.utc),
    )

    collector_2 = _collector(
        repo,
        html_2,
        datetime(2026, 8, 12, 20, 0, tzinfo=timezone.utc),
    )

    collector_1.colectar()
    resultado_2 = collector_2.colectar()

    assert resultado_2.observations_extracted == 1
    assert resultado_2.observations_duplicate == 5

    observaciones = repo.listar_observaciones_precios_comerciales(
        extractor_version="bitz_os_installation_v1"
    )

    valores_pc_todas = [
        o.price_value
        for o in observaciones
        if o.device_type_raw == "PC Todas"
    ]

    assert valores_pc_todas == [35000, 37000]