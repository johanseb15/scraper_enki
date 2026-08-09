from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.infraestructura.downloader import descargar_html
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.cirowhite_parser import parsear_ofertas_cirowhite


class _DownloaderPorDefecto:
    def descargar(self, url: str) -> str:
        return descargar_html(url)


class CiroWhiteScraper(BaseScraper):
    URL = "https://cirowhiteinformatica.com.ar/landing/"
    fuente = "CiroWhite Informática"

    def __init__(self, downloader=None):
        self.downloader = downloader or _DownloaderPorDefecto()
        self.rechazos: list[RechazoIngesta] = []

    def obtener_servicios(self) -> list[OfertaDTO]:
        html = self.downloader.descargar(self.URL)
        self.rechazos = []
        return parsear_ofertas_cirowhite(
            html,
            url_fuente=self.URL,
            rechazos=self.rechazos,
        )
