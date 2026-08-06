from src.aplicacion.dto.oferta_dto import OfertaDTO
# Ajuste de downloader según su ubicación definitiva en infraestructura
from src.infraestructura.downloader import descargar_html
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.venex_parser import VenexParser


class _DownloaderPorDefecto:
    def descargar(self, url: str) -> str:
        return descargar_html(url)


class VenexScraper(BaseScraper):

    URL = "https://www.venex.com.ar/componentes-de-pc"

    def __init__(self, downloader=None, parser=None):
        self.downloader = downloader or _DownloaderPorDefecto()
        self.parser = parser or VenexParser()

    def obtener_servicios(self) -> list[OfertaDTO]:

        html = self.downloader.descargar(self.URL)

        return self.parser.parsear(
            html_content=html,
            url_fuente=self.URL,
        )