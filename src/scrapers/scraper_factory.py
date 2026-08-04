# src/scrapers/scraper_factory.py
from typing import Dict, Type
from src.scrapers.bairescloud_scraper import BairesCloudScraper
from src.scrapers.compragamer_scraper import CompraGamerScraper
from src.scrapers.venex_scraper import VenexScraper

SCRAPERS_REGISTRY: Dict[str, Type] = {
    "venex": VenexScraper,
    "bairescloud": BairesCloudScraper,
    "compragamer": CompraGamerScraper,  # <--- Nuevo proveedor registrado
}


def obtener_scraper(nombre_proveedor: str):
    scraper_cls = SCRAPERS_REGISTRY.get(nombre_proveedor.lower())
    if not scraper_cls:
        raise ValueError(f"Scraper no registrado para el proveedor: {nombre_proveedor}")
    return scraper_cls()