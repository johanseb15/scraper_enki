from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.downloader import descargar_html
from src.extractor import extraer_datos
from src.scrapers.base import BaseScraper


def _convertir_servicio_precio_a_dto(servicio_precio) -> OfertaDTO:
    if isinstance(servicio_precio, OfertaDTO):
        return servicio_precio

    return OfertaDTO(
        empresa_nombre=servicio_precio.empresa,
        provincia=servicio_precio.provincia,
        ciudad=servicio_precio.ciudad,
        fuente=servicio_precio.fuente,
        servicio_raw=servicio_precio.servicio.value,
        precio=servicio_precio.precio_freelance,
        moneda=servicio_precio.moneda,
        fecha_relevamiento=servicio_precio.fecha_relevamiento,
    )


class _DownloaderPorDefecto:
    def descargar(self, url: str) -> str:
        return descargar_html(url)


class VidaInformaticaScraper(BaseScraper):
    URL = "https://vidainformatica.com.ar/listado-de-precios-zona-1/"

    def __init__(self, downloader=None):
        self.downloader = downloader or _DownloaderPorDefecto()

    def obtener_servicios(self) -> list[OfertaDTO]:
        html = self.downloader.descargar(self.URL)
        servicios = extraer_datos(html)
        return [
            _convertir_servicio_precio_a_dto(servicio)
            for servicio in servicios
        ]
