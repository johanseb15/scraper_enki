from datetime import date
from typing import Any, Dict, List

from playwright.sync_api import sync_playwright

from src.aplicacion.acquisition_failure import (
    AcquisitionFailure,
    acquisition_failure_from_exception,
)
from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.compragamer_parser import (
    parsear_ofertas_compragamer,
)


class CompraGamerPlaywrightScraper(BaseScraper):
    """Playwright scraper for the Compra Gamer product catalog."""

    def obtener_servicios(
        self,
        fecha_relevamiento: date | None = None,
    ) -> List[OfertaDTO]:
        if fecha_relevamiento is None:
            fecha_relevamiento = date.today()

        productos_raw: List[Dict[str, Any]] = []
        response_failure: AcquisitionFailure | None = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            def capturar_respuesta(response):
                nonlocal response_failure

                if (
                    response.status == 200
                    and response.url.rstrip("/")
                    == "https://static.compragamer.com/productos"
                ):
                    try:
                        data = response.json()
                    except Exception as exc:
                        response_failure = (
                            acquisition_failure_from_exception(
                                source="compragamer",
                                operation="parse_product_response",
                                exc=exc,
                            )
                        )
                        return

                    if isinstance(data, list):
                        productos_raw.extend(data)

            page.on(
                "response",
                capturar_respuesta,
            )

            page.goto(
                "https://compragamer.com/productos",
                wait_until="networkidle",
                timeout=45000,
            )
            browser.close()

        if response_failure is not None:
            error = RuntimeError(
                "CompraGamer product response could not be parsed"
            )
            error.acquisition_failure = response_failure
            raise error

        if not productos_raw:
            raise RuntimeError(
                "CompraGamer product response was not intercepted"
            )

        return parsear_ofertas_compragamer(
            productos_raw,
            fecha_relevamiento,
        )

    def obtener_ofertas(
        self,
        fecha_relevamiento: date | None = None,
    ) -> List[OfertaDTO]:
        return self.obtener_servicios(
            fecha_relevamiento
        )
