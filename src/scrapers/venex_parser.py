import re
from typing import List
from bs4 import BeautifulSoup
from src.aplicacion.dto.oferta_dto import OfertaDTO


class VenexParser:
    def parsear(self, html_content: str, url_fuente: str = "") -> List[OfertaDTO]:
        soup = BeautifulSoup(html_content, "html.parser")
        ofertas = []

        for item in soup.select(".product-box"):
            titulo_elem = item.select_one(".product-box-title, .product-title")
            precio_elem = item.select_one(".current-price")

            if not titulo_elem or not precio_elem:
                continue

            titulo = titulo_elem.get_text(strip=True)
            precio_texto_original = precio_elem.get_text(strip=True)

            numeros = re.sub(r"[^\d]", "", precio_texto_original)
            precio_numerico = int(numeros) if numeros else 0

            ofertas.append(
                OfertaDTO(
                    empresa_nombre="Venex",
                    servicio_raw=titulo,
                    precio=precio_numerico,
                    precio_raw=precio_texto_original,
                    provincia="Córdoba",
                    ciudad="Córdoba",
                    fuente=url_fuente,
                )
            )

        return ofertas