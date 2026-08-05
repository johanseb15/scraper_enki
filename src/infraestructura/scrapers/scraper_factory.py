# src/infraestructura/scrapers/scraper_factory.py
from typing import Dict, Type

from .base import BaseScraper
from .baires_cloud import BairesCloudScraper
from .compragamer_playwright_scraper import CompraGamerPlaywrightScraper
from .compragamer_scraper import CompraGamerScraper
from .venex import VenexScraper
from .vida_informatica import VidaInformaticaScraper

SCRAPERS_REGISTRY: Dict[str, Type[BaseScraper]] = {
    "bairescloud": BairesCloudScraper,
    "compragamer": CompraGamerPlaywrightScraper,  # Scraper por defecto (Playwright evita bloqueos Cloudflare)
    "compragamer_api": CompraGamerScraper,        # Versión alternativa vía API HTTP
    "venex": VenexScraper,
    "vida_informatica": VidaInformaticaScraper,
}


def obtener_scraper(nombre_proveedor: str) -> BaseScraper:
    """Devuelve una instancia del scraper registrado para el proveedor indicado."""
    scraper_cls = SCRAPERS_REGISTRY.get(nombre_proveedor.lower())
    if not scraper_cls:
        proveedores_disponibles = ", ".join(SCRAPERS_REGISTRY.keys())
        raise ValueError(
            f"Scraper no registrado para: '{nombre_proveedor}'. "
            f"Proveedores disponibles: {proveedores_disponibles}"
        )
    return scraper_cls()