from __future__ import annotations

from datetime import date

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.infraestructura.downloader import descargar_html
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.reed_parser import (
    ContextoReed,
    extraer_contexto_reed,
    parsear_ofertas_reed,
)


class _DownloaderPorDefecto:
    def descargar(self, url: str) -> str:
        return descargar_html(url)


class ReedScraper(BaseScraper):
    URL = "https://www.reed.ar/servicio-tecnico/7137-reparacion-de-pc.html"
    fuente = "REED TECHNOLOGY"

    def __init__(self, downloader=None, fecha_relevamiento: date | None = None):
        self.downloader = downloader or _DownloaderPorDefecto()
        self.fecha_relevamiento = fecha_relevamiento
        self.rechazos: list[RechazoIngesta] = []
        self.contexto: ContextoReed | None = None

    def obtener_servicios(self) -> list[OfertaDTO]:
        html = self.downloader.descargar(self.URL)
        self.rechazos = []
        self.contexto = extraer_contexto_reed(html, self.URL)
        return parsear_ofertas_reed(
            html,
            url_fuente=self.URL,
            fecha_relevamiento=self.fecha_relevamiento,
            rechazos=self.rechazos,
        )
