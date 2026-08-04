from datetime import date
from typing import Any, Dict, List
from playwright.sync_api import sync_playwright

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.scrapers.compragamer_parser import parsear_ofertas_compragamer


class CompraGamerPlaywrightScraper:
    """Scraper Playwright que intercepta el catálogo completo de productos de Compra Gamer."""

    def obtener_ofertas(self, fecha_relevamiento: date | None = None) -> List[OfertaDTO]:
        if fecha_relevamiento is None:
            fecha_relevamiento = date.today()

        productos_raw: List[Dict[str, Any]] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            def capturar_respuesta(response):
                # Captura estricta del JSON final de productos (evitando otros endpoints estáticos)
                if response.status == 200 and response.url.rstrip("/") == "https://static.compragamer.com/productos":
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            productos_raw.extend(data)
                    except Exception:
                        pass

            page.on("response", capturar_respuesta)

            page.goto("https://compragamer.com/productos", wait_until="networkidle", timeout=45000)
            browser.close()

        if not productos_raw:
            raise RuntimeError("No se interceptó la respuesta de https://static.compragamer.com/productos")

        return parsear_ofertas_compragamer(productos_raw, fecha_relevamiento)