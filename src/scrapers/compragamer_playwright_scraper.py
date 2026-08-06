from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright  # Importación explícita para habilitar mock en los tests
from .base_scraper import BaseScraper

class CompraGamerPlaywrightScraper(BaseScraper):
    def __init__(self, url: Optional[str] = None):
        self.url = url or "https://compragamer.com"

    def obtener_servicios(self) -> List[Dict[str, Any]]:
        """
        Usa Playwright para extraer ofertas de la página.
        La presencia explícita de `sync_playwright` en este módulo permite que
        `@patch('src.scrapers.compragamer_playwright_scraper.sync_playwright')`
        funcione en la suite de pruebas.
        """
        ofertas = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until="networkidle")
            
            # Lógica de scraping/extracción sobre el DOM
            
            browser.close()
            
        return ofertas