from src.downloader import descargar_html
from src.extractor import extraer_datos
from src.scrapers.base import BaseScraper


class _DownloaderPorDefecto:
    def descargar(self, url: str) -> str:
        return descargar_html(url)


class VidaInformaticaScraper(BaseScraper):
    URL = "https://vidainformatica.com.ar/listado-de-precios-zona-1/"

    def __init__(self, downloader=None):
        self.downloader = downloader or _DownloaderPorDefecto()

    def obtener_servicios(self):
        html = self.downloader.descargar(self.URL)
        return extraer_datos(html)