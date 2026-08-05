from datetime import date
import re
from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO


def _limpiar_precio(precio_str: str) -> int:
    """Extrae y convierte el valor numérico entero de una cadena de precio como '$ 150.000'."""
    numeros = re.sub(r"[^\d]", "", precio_str)
    return int(numeros) if numeros else 0


class VenexParser:
    """Parser encargado de transformar HTML de Venex en OfertaDTO."""

    def parsear(
        self,
        html_content: str,
        url_fuente: str,
        fecha_relevamiento: date | None = None,
    ) -> list[OfertaDTO]:
        if fecha_relevamiento is None:
            fecha_relevamiento = date.today()

        soup = BeautifulSoup(html_content, "html.parser")
        tarjetas = soup.select(".product-box")

        ofertas: list[OfertaDTO] = []

        for tarjeta in tarjetas:
            nodo_titulo = (
                tarjeta.select_one(".product-box-title")
                or tarjeta.select_one(".product-title")
                or tarjeta.select_one("h3")
            )

            nodo_precio = tarjeta.select_one(".current-price")

            if not nodo_titulo or not nodo_precio:
                continue

            precio_texto = nodo_precio.get_text(strip=True)
            precio_int = _limpiar_precio(precio_texto)

            if precio_int <= 0:
                continue

            oferta = OfertaDTO(
                empresa_nombre="Venex",
                provincia="Córdoba",
                ciudad="Córdoba",
                servicio_raw=nodo_titulo.get_text(strip=True),
                precio=precio_int,
                moneda="ARS",
                fecha_relevamiento=fecha_relevamiento,
                fuente=url_fuente,
            )

            ofertas.append(oferta)

        return ofertas