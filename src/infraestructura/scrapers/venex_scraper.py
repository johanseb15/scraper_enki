from typing import Callable, Optional
from src.aplicacion.dto.oferta_dto import OfertaDTO


class VenexScraper:

    def __init__(
        self,
        url_base: str = "https://www.venex.com.ar",
        downloader: Optional[Callable[[str], str]] = None,
    ):
        self.url_base = url_base
        self.downloader = downloader

    def obtener_ofertas(self) -> list[OfertaDTO]:
        ofertas: list[OfertaDTO] = []

        # Ejemplo / Estructura base de extracción
        # titulo = "Servicio de Mantenimiento / Producto"
        # precio_numerico = 15000.0
        # precio_texto_original = "$15.000"
        # url_fuente = "https://www.venex.com.ar/..."

        # Asegurar que precio_raw nunca sea None
        # precio_raw_seguro = precio_texto_original if precio_texto_original is not None else str(precio_numerico or "")

        # ofertas.append(
        #     OfertaDTO(
        #         empresa_nombre="Venex",
        #         servicio_raw=titulo,
        #         precio=precio_numerico,
        #         precio_raw=precio_raw_seguro,
        #         provincia="Córdoba",
        #         ciudad="Córdoba",
        #         fuente=url_fuente,
        #     )
        # )

        return ofertas