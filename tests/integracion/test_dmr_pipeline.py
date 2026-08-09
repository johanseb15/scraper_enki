from datetime import date
from pathlib import Path

from src.infraestructura.scrapers.dmr import DMRScraper
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.pipeline import PipelineOfertas


FIXTURE = Path(__file__).parents[1] / "fixtures" / "dmr_mantenimiento.html"


class DownloaderFixture:
    def descargar(self, _url: str) -> str:
        return FIXTURE.read_text(encoding="utf-8")


def test_dmr_atraviesa_pipeline_y_sqlite_sin_perder_precio_raw(tmp_path):
    repositorio = RepositorioSQLiteOfertas(tmp_path / "dmr.db")
    scraper = DMRScraper(
        downloader=DownloaderFixture(),
        fecha_relevamiento=date(2026, 8, 9),
    )

    ofertas = PipelineOfertas(
        scrapers=[scraper], repositorio=repositorio
    ).ejecutar()
    persistidas = repositorio.obtener_todas()

    assert len(ofertas) == 3
    assert len(persistidas) == 3
    assert {(o.servicio_raw, o.precio.valor, o.precio_raw) for o in persistidas} == {
        ("Formateo e instalación de SO sin BackUp", 49700, "$49.700"),
        ("Eliminación de malware / virus", 29000, "$29.000"),
        ("Visita a domicilio x 1 hora", 24300, "$24.300"),
    }
    assert all(o.empresa.nombre == "Dmr Web Design" for o in persistidas)
    assert all(o.empresa.provincia == "Mendoza" for o in persistidas)
    assert all(o.empresa.ciudad == "Mendoza Capital" for o in persistidas)
    assert all(o.fecha_relevamiento == date(2026, 8, 9) for o in persistidas)
