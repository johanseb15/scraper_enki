# src/infraestructura/scrapers/compragamer_scraper.py
from datetime import date
from typing import List
import requests

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.compragamer_parser import parsear_ofertas_compragamer

URL_COMPRAGAMER_API = "https://static.compragamer.com/productos"


class CompraGamerScraper(BaseScraper):
    """Scraper HTTP directo para la API REST de Compra Gamer."""

    def __init__(self, url_api: str = URL_COMPRAGAMER_API):
        self.url_api = url_api

    def obtener_servicios(self, fecha_relevamiento: date | None = None) -> List[OfertaDTO]:
        """Obtiene y normaliza las ofertas consultando la API pública."""
        if fecha_relevamiento is None:
            fecha_relevamiento = date.today()

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://compragamer.com/",
        }

        response = requests.get(self.url_api, headers=headers, timeout=15)
        
        # Validación de tipo de contenido antes de parsear
        if "json" not in response.headers.get("Content-Type", "").lower():
            print(f"⚠️ Status Code: {response.status_code}")
            print(f"⚠️ Content-Type: {response.headers.get('Content-Type')}")
            print(f"⚠️ Primeros 300 caracteres recibidos:\n{response.text[:300]}")
            raise ValueError("La respuesta del servidor no es JSON (posible bloqueo bot/Cloudflare).")

        datos = response.json()
        return parsear_ofertas_compragamer(datos, fecha_relevamiento)

    # Alias por compatibilidad
    def obtener_ofertas(self, fecha_relevamiento: date | None = None) -> List[OfertaDTO]:
        return self.obtener_servicios(fecha_relevamiento)
