from src.scrapers.base_scraper import BaseScraper
from src.aplicacion.dto.oferta_dto import OfertaDTO

class VenexScraper(BaseScraper):
    """Scraper para la tienda Venex."""

    def __init__(self, downloader=None):
        self.downloader = downloader

    def obtener_servicios(self) -> list[OfertaDTO]:
        """Extrae las ofertas de Venex utilizando el downloader inyectado."""
        if self.downloader:
            html = self.downloader.descargar("https://www.venex.com.ar")
            # Aquí se puede integrar el parser correspondiente si se requiere
            
        return []