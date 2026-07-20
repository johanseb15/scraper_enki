from src.downloader import descargar_html
from src.extractor import extraer_datos


class VidaInformaticaScraper:

    URL = "https://vidainformatica.com.ar/listado-de-precios-zona-1/"

    def obtener_servicios(self):
        html = descargar_html(self.URL)
        return extraer_datos(html)