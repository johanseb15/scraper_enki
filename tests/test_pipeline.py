from pathlib import Path

from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.pipeline import PipelineOfertas
from src.presentacion import generar_reporte_texto
from src.reporte import generar_resumen_servicio
from src.scrapers.vida_informatica import VidaInformaticaScraper


class DownloaderFixture:
    def __init__(self, html: str):
        self.html = html

    def descargar(self, url: str) -> str:
        return self.html


def test_pipeline_completo_de_html_a_reporte(tmp_path):
    ruta_html = Path(__file__).parent / "fixtures" / "vida_informatica_zona1.html"
    html = ruta_html.read_text(encoding="utf-8")
    scraper = VidaInformaticaScraper(downloader=DownloaderFixture(html))
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "pipeline_reporte.db")
    )
    pipeline = PipelineOfertas(
        scrapers=[scraper],
        repositorio=repositorio,
    )

    ofertas = pipeline.ejecutar()
    persistidas = repositorio.obtener_todas()
    resumen = generar_resumen_servicio(
        persistidas,
        "Eliminación de malware",
    )
    reporte = generar_reporte_texto(resumen)

    assert len(persistidas) == len(ofertas)
    assert resumen["cantidad"] == 1
    assert resumen["precio_minimo"] == 29816
    assert "Eliminación de malware" in reporte
    assert "29816" in reporte
