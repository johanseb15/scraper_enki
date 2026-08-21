from datetime import datetime, timezone

import requests

from src.aplicacion.colector_precios_batch import (
    FuentePricing,
    colectar_fuentes_pricing,
)
from src.infraestructura.scrapers.generic_price_extractor import (
    extraer_observaciones_precio_genericas,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


WHEN = datetime(
    2026, 8, 13, 14, 0,
    tzinfo=timezone.utc,
)


HTML_A = """
<html>
  <body>
    <table>
      <tr>
        <td>Formateo PC</td>
        <td>$35.000</td>
      </tr>
      <tr>
        <td>Limpieza Notebook</td>
        <td>$42.000</td>
      </tr>
    </table>
  </body>
</html>
"""


HTML_B = """
<html>
  <body>
    <div>
      <h3>Instalación de sistema operativo</h3>
      <strong>$50.000</strong>
    </div>
  </body>
</html>
"""


class DownloaderPorURLFake:
    def __init__(self, respuestas):
        self.respuestas = respuestas

    def descargar(self, url: str) -> str:
        respuesta = self.respuestas[url]

        if isinstance(respuesta, Exception):
            raise respuesta

        return respuesta


def test_batch_colecta_varias_fuentes(tmp_path):
    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    fuentes = [
        FuentePricing(
            source="fuente_a",
            provider="Proveedor A",
            url="https://a.example/precios",
            province="Córdoba",
            city="Córdoba",
        ),
        FuentePricing(
            source="fuente_b",
            provider="Proveedor B",
            url="https://b.example/precios",
            province="Mendoza",
            city="Mendoza",
        ),
    ]

    downloader = DownloaderPorURLFake(
        {
            "https://a.example/precios": HTML_A,
            "https://b.example/precios": HTML_B,
        }
    )

    resultado = colectar_fuentes_pricing(
        fuentes,
        repositorio=repo,
        downloader=downloader,
        extractor=extraer_observaciones_precio_genericas,
        reloj=lambda: WHEN,
    )

    assert resultado.sources_attempted == 2
    assert resultado.sources_succeeded == 2
    assert resultado.sources_failed == 0

    assert resultado.raw_docs_acquired == 2
    assert resultado.observations_extracted == 3
    assert resultado.exact_prices == 3

    raws_a = repo.listar_documentos_raw(
        source="fuente_a"
    )
    raws_b = repo.listar_documentos_raw(
        source="fuente_b"
    )

    assert len(raws_a) == 1
    assert len(raws_b) == 1


def test_batch_continua_si_una_fuente_falla(tmp_path):
    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    fuentes = [
        FuentePricing(
            source="fuente_ok",
            provider="Proveedor OK",
            url="https://ok.example/precios",
            province="Santa Fe",
            city="Rosario",
        ),
        FuentePricing(
            source="fuente_rota",
            provider="Proveedor Roto",
            url="https://broken.example/precios",
            province="Salta",
            city="Salta",
        ),
    ]

    downloader = DownloaderPorURLFake(
        {
            "https://ok.example/precios": HTML_B,
            "https://broken.example/precios": RuntimeError(
                "timeout"
            ),
        }
    )

    resultado = colectar_fuentes_pricing(
        fuentes,
        repositorio=repo,
        downloader=downloader,
        extractor=extraer_observaciones_precio_genericas,
        reloj=lambda: WHEN,
    )

    assert resultado.sources_attempted == 2
    assert resultado.sources_succeeded == 1
    assert resultado.sources_failed == 1

    assert resultado.observations_extracted == 1

    assert len(resultado.failures) == 1
    assert resultado.failures[0].source == "fuente_rota"
    assert "timeout" in resultado.failures[0].error


def test_batch_registra_fuente_con_geografia(tmp_path):
    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    fuentes = [
        FuentePricing(
            source="cordoba_test",
            provider="Técnico Córdoba",
            url="https://cordoba.example/precios",
            province="Córdoba",
            city="Villa María",
        )
    ]

    downloader = DownloaderPorURLFake(
        {
            "https://cordoba.example/precios": HTML_B,
        }
    )

    colectar_fuentes_pricing(
        fuentes,
        repositorio=repo,
        downloader=downloader,
        extractor=extraer_observaciones_precio_genericas,
        reloj=lambda: WHEN,
    )

    raws = repo.listar_documentos_raw(
        source="cordoba_test"
    )

    assert len(raws) == 1

    assert raws[0].metadata["province"] == "Córdoba"
    assert raws[0].metadata["city"] == "Villa María"
    assert raws[0].metadata["provider_name"] == "Técnico Córdoba"


def test_batch_es_idempotente(tmp_path):
    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    fuentes = [
        FuentePricing(
            source="fuente_a",
            provider="Proveedor A",
            url="https://a.example/precios",
            province="Córdoba",
            city="Córdoba",
        )
    ]

    downloader = DownloaderPorURLFake(
        {
            "https://a.example/precios": HTML_A,
        }
    )

    colectar_fuentes_pricing(
        fuentes,
        repositorio=repo,
        downloader=downloader,
        extractor=extraer_observaciones_precio_genericas,
        reloj=lambda: WHEN,
    )

    resultado = colectar_fuentes_pricing(
        fuentes,
        repositorio=repo,
        downloader=downloader,
        extractor=extraer_observaciones_precio_genericas,
        reloj=lambda: WHEN,
    )

    assert resultado.sources_attempted == 1
    assert resultado.sources_succeeded == 1

    assert resultado.raw_docs_acquired == 0
    assert resultado.raw_docs_duplicate == 1

    assert resultado.observations_extracted == 0
    assert resultado.observations_duplicate == 2

def test_batch_clasifica_fallo_tls_sin_ocultarlo(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    fuente = FuentePricing(
        source="tls_fail",
        provider="TLS Fail",
        url="https://tls.example/precios",
        province="Córdoba",
        city="Córdoba",
    )
    downloader = DownloaderPorURLFake(
        {fuente.url: requests.exceptions.SSLError("certificate verify failed")}
    )

    resultado = colectar_fuentes_pricing(
        [fuente],
        repositorio=repo,
        downloader=downloader,
        extractor=extraer_observaciones_precio_genericas,
        reloj=lambda: WHEN,
    )

    assert resultado.sources_failed == 1
    assert resultado.failures[0].error_type == "TLS_CERTIFICATE_ERROR"
    assert "certificate verify failed" in resultado.failures[0].error


def test_batch_clasifica_dns_y_timeout_separados_de_tls(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    fuentes = [
        FuentePricing(
            source="dns_fail",
            provider="DNS Fail",
            url="https://dns.example/precios",
            province="Córdoba",
            city="Córdoba",
        ),
        FuentePricing(
            source="timeout_fail",
            provider="Timeout Fail",
            url="https://timeout.example/precios",
            province="Córdoba",
            city="Córdoba",
        ),
    ]
    downloader = DownloaderPorURLFake(
        {
            fuentes[0].url: requests.exceptions.ConnectionError(
                "NameResolutionError: Failed to resolve"
            ),
            fuentes[1].url: requests.exceptions.Timeout("timed out"),
        }
    )

    resultado = colectar_fuentes_pricing(
        fuentes,
        repositorio=repo,
        downloader=downloader,
        extractor=extraer_observaciones_precio_genericas,
        reloj=lambda: WHEN,
    )

    by_source = {failure.source: failure for failure in resultado.failures}
    assert by_source["dns_fail"].error_type == "DNS_ERROR"
    assert by_source["timeout_fail"].error_type == "TIMEOUT"
