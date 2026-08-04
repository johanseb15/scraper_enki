from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO


class VenexParser:
    """Parser encargado de transformar HTML de Venex en OfertaDTO."""

    def parsear(self, html_content: str, url_fuente: str) -> list[OfertaDTO]:
        soup = BeautifulSoup(html_content, "html.parser")

        tarjetas = soup.select(".product-box")

        ofertas = []

        for tarjeta in tarjetas:
            nodo_titulo = (
                tarjeta.select_one(".product-box-title")
                or tarjeta.select_one(".product-title")
                or tarjeta.select_one("h3")
            )

            nodo_precio = tarjeta.select_one(".current-price")

            if not nodo_titulo or not nodo_precio:
                continue

            oferta = OfertaDTO(
                empresa_nombre="Venex",
                provincia="Córdoba",
                ciudad="Córdoba",
                servicio_raw=nodo_titulo.get_text(strip=True),
                precio_raw=nodo_precio.get_text(strip=True),
                fuente=url_fuente,
            )

            ofertas.append(oferta)

        return ofertas