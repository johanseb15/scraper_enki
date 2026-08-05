from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.downloader import descargar_html
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.vida_informatica_parser import extraer_datos_vida_informatica


class _DownloaderPorDefecto:
    def descargar(self, url: str) -> str:
        return descargar_html(url)


class VidaInformaticaScraper(BaseScraper):
    URL = "https://vidainformatica.com.ar/listado-de-precios-zona-1/"

    def __init__(self, downloader=None):
        self.downloader = downloader or _DownloaderPorDefecto()

    def obtener_servicios(self) -> list[OfertaDTO]:
        html = self.downloader.descargar(self.URL)
        return extraer_datos_vida_informatica(html, url_fuente=self.URL)