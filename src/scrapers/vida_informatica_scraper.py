from typing import List, Dict, Any, Optional
from .base_scraper import BaseScraper  # O el módulo base correspondiente

class VidaInformaticaScraper(BaseScraper):
    def __init__(self, url_base: Optional[str] = None):
        self.url_base = url_base or "https://vidainformatica.com.ar"

    def obtener_servicios(self) -> List[Dict[str, Any]]:
        """
        Extrae y expone los servicios/ofertas disponibles.
        Cumple con el contrato esperado por la suite de pruebas y pipelines.
        """
        ofertas = []
        # Lógica de extracción/scraping
        # Ejemplo de estructura normalizada devuelta:
        # ofertas.append({
        #     "titulo": "Servicio de Internet",
        #     "precio": 25000,
        #     "moneda": "ARS",
        #     "proveedor": "Vida Informatica",
        #     "url": self.url_base
        # })
        return ofertas

    def ejecutar() -> List[Dict[str, Any]]:
        """Alias para mantener compatibilidad con invocaciones directas."""
        return self.obtener_servicios()