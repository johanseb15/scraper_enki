from src.scrapers.base_scraper import BaseScraper
from src.aplicacion.dto.oferta_dto import OfertaDTO

class VidaInformaticaScraper(BaseScraper):
    """Scraper para la tienda Vida Informática."""

    def __init__(self, downloader=None):
        self.downloader = downloader

    def obtener_servicios(self) -> list[OfertaDTO]:
        """Extrae las ofertas de Vida Informática utilizando el downloader si está presente."""
        if self.downloader:
            # Lógica usando el downloader inyectado
            html = self.downloader.descargar("https://www.vidainformatica.com.ar")
            # Aquí iría el parsing o delegación a parser
        
        # Retorno de ejemplo o implementación real existente
        return []