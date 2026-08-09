from __future__ import annotations

from datetime import date

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.infraestructura.downloader import descargar_html
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.dmr_parser import (
    ContextoDMR,
    extraer_contexto_dmr,
    parsear_ofertas_dmr,
)


class _DownloaderPorDefecto:
    def descargar(self, url: str) -> str:
        return descargar_html(url)


class DMRScraper(BaseScraper):
    URL = "https://dmrwebdesign.com.ar/mantenimiento.html"
    fuente = "DMR Web Design"

    def __init__(self, downloader=None, fecha_relevamiento: date | None = None):
        self.downloader = downloader or _DownloaderPorDefecto()
        self.fecha_relevamiento = fecha_relevamiento
        self.rechazos: list[RechazoIngesta] = []
        self.contexto: ContextoDMR | None = None

    def obtener_servicios(self) -> list[OfertaDTO]:
        html = self.downloader.descargar(self.URL)
        self.rechazos = []
        self.contexto = extraer_contexto_dmr(html)
        return parsear_ofertas_dmr(
            html,
            url_fuente=self.URL,
            fecha_relevamiento=self.fecha_relevamiento,
            rechazos=self.rechazos,
        )
