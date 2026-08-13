from datetime import datetime, timezone

from src.aplicacion.colector_precios_os_jadetech import (
    ColectorPreciosOSJadetech,
)
from src.infraestructura.scrapers.generic_price_extractor import (
    EXTRACTOR_VERSION,
    extraer_observaciones_precio_genericas,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


URL = "https://ejemplo.com/servicios"
SOURCE = "ejemplo_generic"
PROVIDER = "Ejemplo Técnico"


class DownloaderFake:
    def __init__(self, html: str):
        self.html = html

    def descargar(self, url: str) -> str:
        assert url == URL
        return self.html


def _parser(
    html: str,
    *,
    source_url: str,
    raw_document_id: int,
    retrieved_at: datetime,
    content_hash: str | None = None,
):
    return extraer_observaciones_precio_genericas(
        html,
        source=SOURCE,
        provider=PROVIDER,
        source_url=source_url,
        raw_document_id=raw_document_id,
        retrieved_at=retrieved_at,
        content_hash=content_hash,
    )


def _collector(repo, html, when):
    return ColectorPreciosOSJadetech(
        repositorio=repo,
        downloader=DownloaderFake(html),
        parser_observaciones=_parser,
        reloj=lambda: when,
        source_url=URL,
        source=SOURCE,
        provider=PROVIDER,
        extractor_version=EXTRACTOR_VERSION,
        source_notes="Generic automatic pricing source",
    )


def test_collector_generico_preserva_raw_y_persiste_precios(tmp_path):
    html = """
    <html>
      <body>
        <table>
          <tr>
            <td>Formateo PC</td>
            <td>$35.000</td>
          </tr>
          <tr>
            <td>Limpieza notebook</td>
            <td>$42.000</td>
          </tr>
        </table>
      </body>
    </html>
    """

    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    collector = _collector(
        repo,
        html,
        datetime(
            2026, 8, 13, 13, 0,
            tzinfo=timezone.utc,
        ),
    )

    resultado = collector.colectar()

    assert resultado.raw_docs_acquired == 1
    assert resultado.observations_extracted == 2
    assert resultado.exact_prices == 2
    assert resultado.indeterminate == 2

    raws = repo.listar_documentos_raw(
        source=SOURCE
    )

    assert len(raws) == 1
    assert raws[0].raw_content == html

    observaciones = (
        repo.listar_observaciones_precios_comerciales(
            extractor_version=EXTRACTOR_VERSION
        )
    )

    assert len(observaciones) == 2
    assert {
        observacion.price_value
        for observacion in observaciones
    } == {
        35000,
        42000,
    }


def test_collector_generico_es_idempotente(tmp_path):
    html = """
    <html>
      <body>
        <div>
          <h3>Formateo PC</h3>
          <strong>$35.000</strong>
        </div>
      </body>
    </html>
    """

    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    collector = _collector(
        repo,
        html,
        datetime(
            2026, 8, 13, 13, 0,
            tzinfo=timezone.utc,
        ),
    )

    collector.colectar()
    resultado = collector.colectar()

    assert resultado.raw_docs_acquired == 0
    assert resultado.raw_docs_duplicate == 1
    assert resultado.observations_extracted == 0
    assert resultado.observations_duplicate == 1


def test_collector_generico_no_duplica_economia_si_cambia_raw(tmp_path):
    html_1 = """
    <html>
      <body>
        <div>
          <h3>Formateo PC</h3>
          <strong>$35.000</strong>
        </div>
      </body>
    </html>
    """

    html_2 = html_1.replace(
        "<body>",
        "<body><!-- cambio irrelevante -->",
    )

    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    _collector(
        repo,
        html_1,
        datetime(
            2026, 8, 13, 13, 0,
            tzinfo=timezone.utc,
        ),
    ).colectar()

    _collector(
        repo,
        html_2,
        datetime(
            2026, 8, 13, 14, 0,
            tzinfo=timezone.utc,
        ),
    ).colectar()

    raws = repo.listar_documentos_raw(
        source=SOURCE
    )

    observaciones = (
        repo.listar_observaciones_precios_comerciales(
            extractor_version=EXTRACTOR_VERSION
        )
    )

    assert len(raws) == 2
    assert len(observaciones) == 1


def test_collector_generico_detecta_cambio_real_de_precio(tmp_path):
    html_1 = """
    <html>
      <body>
        <div>
          <h3>Formateo PC</h3>
          <strong>$35.000</strong>
        </div>
      </body>
    </html>
    """

    html_2 = html_1.replace(
        "$35.000",
        "$38.000",
    )

    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    _collector(
        repo,
        html_1,
        datetime(
            2026, 8, 13, 13, 0,
            tzinfo=timezone.utc,
        ),
    ).colectar()

    _collector(
        repo,
        html_2,
        datetime(
            2026, 8, 13, 14, 0,
            tzinfo=timezone.utc,
        ),
    ).colectar()

    observaciones = (
        repo.listar_observaciones_precios_comerciales(
            extractor_version=EXTRACTOR_VERSION
        )
    )

    assert sorted(
        observacion.price_value
        for observacion in observaciones
    ) == [
        35000,
        38000,
    ]
