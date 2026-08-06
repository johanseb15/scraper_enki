import urllib.request
from typing import Callable, Optional
from src.aplicacion.dto.oferta_dto import OfertaDTO


def descargar_html(url: str) -> str:
    """Función a nivel de módulo para descargar HTML (permite mock/patching en tests)."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8")


class VidaInformaticaScraper:

    def __init__(
        self,
        url_base: str = "https://vidainformatica.com.ar",
        downloader: Optional[Callable[[str], str]] = None,
    ):
        self.url_base = url_base
        self.downloader = downloader or descargar_html

    def obtener_ofertas(self) -> list[OfertaDTO]:
        ofertas: list[OfertaDTO] = []

        try:
            html = self.downloader(self.url_base)
            # Lógica de extracción de contenido HTML si corresponde
        except Exception:
            pass

        return ofertas