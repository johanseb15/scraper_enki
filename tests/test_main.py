from datetime import date
from pathlib import Path

import pytest

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.extractor import extraer_datos
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.main import ejecutar
from src.scrapers.base import BaseScraper


@pytest.fixture
def servicios_desde_fixture():
    """Carga el fixture local y lo parsea para simular la respuesta del scraper."""
    ruta_html = Path(__file__).parent / "fixtures" / "vida_informatica_zona1.html"
    html = ruta_html.read_text(encoding="utf-8")
    return extraer_datos(html)


class ScraperConDatos(BaseScraper):
    def __init__(self, ofertas: list[OfertaDTO]):
        self.ofertas = ofertas

    def obtener_servicios(self) -> list[OfertaDTO]:
        return self.ofertas


def test_ejecutar_devuelve_un_reporte(tmp_path, servicios_desde_fixture):
    db_temporal = str(tmp_path / "test_enki.db")

    reporte = ejecutar(
        ruta_db=db_temporal,
        scrapers=[ScraperConDatos(servicios_desde_fixture)],
    )

    assert isinstance(reporte, str)
    assert len(reporte) > 0


def test_main_ejecuta_pipeline_completo(tmp_path, servicios_desde_fixture):
    db_temporal = str(tmp_path / "test_enki.db")

    reporte = ejecutar(
        ruta_db=db_temporal,
        scrapers=[ScraperConDatos(servicios_desde_fixture)],
    )

    assert "Eliminación de malware" in reporte


def test_ejecutar_persiste_datos_de_ambos_scrapers(tmp_path):
    db_temporal = str(tmp_path / "test_enki.db")
    fecha = date(2026, 7, 20)
    servicio_vida = OfertaDTO(
        empresa_nombre="Vida informatica",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio_raw="Eliminación de malware",
        precio=29816,
        precio_raw="$ 29.816",
        moneda="ARS",
        fecha_relevamiento=fecha,
        fuente="Vida Informática",
    )
    servicio_baires = OfertaDTO(
        empresa_nombre="BairesCloud",
        provincia="Buenos Aires",
        ciudad="Buenos Aires",
        servicio_raw="Eliminación de malware / spyware",
        precio=25000,
        precio_raw="$ 25.000",
        moneda="ARS",
        fecha_relevamiento=fecha,
        fuente="BairesCloud",
    )

    ejecutar(
        ruta_db=db_temporal,
        scrapers=[
            ScraperConDatos([servicio_vida]),
            ScraperConDatos([servicio_baires]),
        ],
    )

    repositorio = RepositorioSQLiteOfertas(ruta_db=db_temporal)
    empresas_guardadas = {
        oferta.empresa.nombre for oferta in repositorio.obtener_todas()
    }

    assert empresas_guardadas == {"Vida Informatica", "BairesCloud"}


class ScraperDummy(BaseScraper):
    """Scraper de prueba para validar inyección dinámica."""

    def __init__(self, empresa: str):
        self.empresa = empresa

    def obtener_servicios(self) -> list[OfertaDTO]:
        return [
            OfertaDTO(
                empresa_nombre=self.empresa,
                provincia="Córdoba",
                ciudad="Córdoba",
                servicio_raw="Limpieza de virus",
                precio=15000,
                precio_raw="$ 15.000",
                moneda="ARS",
                fecha_relevamiento=date.today(),
                fuente="https://test.com",
            )
        ]


def test_ejecutar_procesa_lista_dinamica_de_scrapers(tmp_path):
    db_path = str(tmp_path / "test_enki.db")
    scrapers = [ScraperDummy("Empresa Alpha"), ScraperDummy("Empresa Beta")]

    reporte = ejecutar(ruta_db=db_path, scrapers=scrapers)

    assert "Empresa Alpha" in reporte
    assert "Empresa Beta" in reporte


class ScraperFallado(BaseScraper):
    """Scraper que simula una caída de red o error de parsing."""

    def obtener_servicios(self) -> list[OfertaDTO]:
        raise RuntimeError("Error de conexión con el sitio destino")


def test_ejecutar_tolera_fallo_de_un_scraper_y_continua(tmp_path):
    db_path = str(tmp_path / "test_enki.db")
    scrapers = [ScraperFallado(), ScraperDummy("Empresa Resiliente")]

    reporte = ejecutar(ruta_db=db_path, scrapers=scrapers)

    assert "Empresa Resiliente" in reporte


def test_ejecutar_registra_metricas_de_exito_y_fallo(tmp_path):
    db_path = str(tmp_path / "test_enki.db")
    scrapers = [ScraperFallado(), ScraperDummy("Empresa Resiliente")]

    resultado = ejecutar(ruta_db=db_path, scrapers=scrapers)

    assert resultado.metricas.exitosos == ["ScraperDummy"]
    assert resultado.metricas.fallidos == ["ScraperFallado"]
    assert resultado.metricas.total == 2
