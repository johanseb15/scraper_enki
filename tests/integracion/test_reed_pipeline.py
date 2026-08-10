from datetime import date
from pathlib import Path

from src.dominio.servicios import ServicioCanonico
from src.infraestructura.scrapers.reed import ReedScraper
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.pipeline import PipelineOfertas


FIXTURE = Path(__file__).parents[1] / "fixtures" / "reed_reparacion_pc.html"


class DownloaderFixture:
    def descargar(self, _url: str) -> str:
        return FIXTURE.read_text(encoding="utf-8")


def test_reed_atraviesa_pipeline_y_sqlite_sin_persistir_el_precio_cero(tmp_path):
    repositorio = RepositorioSQLiteOfertas(tmp_path / "reed.db")
    scraper = ReedScraper(
        downloader=DownloaderFixture(),
        fecha_relevamiento=date(2026, 8, 9),
    )

    ofertas = PipelineOfertas(
        scrapers=[scraper], repositorio=repositorio
    ).ejecutar()
    persistidas = repositorio.obtener_todas()

    assert len(ofertas) == 12
    assert len(persistidas) == 12
    assert all(oferta.precio.valor > 0 for oferta in persistidas)
    assert {(o.servicio_raw, o.precio.valor, o.precio_raw) for o in persistidas} >= {
        (
            "Formateo con backup hasta 150GB (+$18150 por prog diseño)",
            63600,
            "$63.600",
        ),
        ("Limpieza de Virus malaware e Inicio", 38200, "$38.200"),
        ("Actualizacion de BIOS", 44500, "$44.500"),
    }
    assert all(o.empresa.nombre == "Reed Technology" for o in persistidas)
    assert all(o.empresa.provincia == "Córdoba" for o in persistidas)
    assert all(o.empresa.ciudad == "Córdoba" for o in persistidas)
    assert all(o.fecha_relevamiento == date(2026, 8, 9) for o in persistidas)
    assert ServicioCanonico.FORMATEO in {o.servicio for o in persistidas}
    assert ServicioCanonico.MALWARE in {o.servicio for o in persistidas}
    assert len(scraper.rechazos) == 1
