from datetime import date
from pathlib import Path

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.reed import ReedScraper


FIXTURE = Path(__file__).parents[1] / "fixtures" / "reed_reparacion_pc.html"


class DownloaderFixture:
    def __init__(self):
        self.urls: list[str] = []

    def descargar(self, url: str) -> str:
        self.urls.append(url)
        return FIXTURE.read_text(encoding="utf-8")


def test_reed_usa_downloader_inyectado_y_expone_rechazo_del_cero():
    downloader = DownloaderFixture()
    scraper = ReedScraper(
        downloader=downloader,
        fecha_relevamiento=date(2026, 8, 9),
    )

    dtos = scraper.obtener_servicios()

    assert isinstance(scraper, BaseScraper)
    assert downloader.urls == [ReedScraper.URL]
    assert len(dtos) == 12
    assert all(isinstance(dto, OfertaDTO) for dto in dtos)
    assert dtos[0].fecha_relevamiento == date(2026, 8, 9)
    assert scraper.fuente == "REED TECHNOLOGY"
    assert len(scraper.rechazos) == 1
    assert "PRECIO_CERO_LITERAL" in scraper.rechazos[0].razon
    assert scraper.contexto is not None
    assert scraper.contexto.precio_producto_raw == "$ 0"
