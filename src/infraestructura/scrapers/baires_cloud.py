from datetime import date
import re

from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.scrapers.base import BaseScraper
# Si el downloader pasó a infraestructura:
# from src.infraestructura.downloader import descargar_html 
from src.infraestructura.downloader import descargar_html 


class _DownloaderPorDefecto:

    def descargar(self, url: str) -> str:
        return descargar_html(url)


class BairesCloudScraper(BaseScraper):
    URL = "https://bairescloud.ar/servicio-tecnico.php"

    def __init__(self, downloader=None):
        self.downloader = downloader or _DownloaderPorDefecto()

    def obtener_servicios(self) -> list[OfertaDTO]:
        html = self.downloader.descargar(self.URL)

        return extraer_precios_bairescloud(
            html,
            fecha_relevamiento=date.today(),
        )


def _a_numero(precio: str) -> int:
    coincidencia = re.search(r"\d[\d.]*,\d{2}", precio)

    if not coincidencia:
        raise ValueError(
            f"No se pudo extraer un precio válido: {precio!r}"
        )

    limpio = (
        coincidencia.group()
        .replace(".", "")
        .replace(",", ".")
    )

    return int(float(limpio))


def extraer_precios_bairescloud(
    html: str,
    fecha_relevamiento: date,
) -> list[OfertaDTO]:
    soup = BeautifulSoup(html, "html.parser")

    resultados = []

    for tabla in soup.find_all("table"):
        encabezados = [
            encabezado.get_text(strip=True).lower()
            for encabezado in tabla.find_all("th")
        ]

        if encabezados != ["servicio", "equipo", "precio"]:
            continue

        cuerpos = tabla.find_all("tbody")

        if not cuerpos:
            continue

        for fila in cuerpos[0].find_all("tr"):
            celdas = fila.find_all("td")

            if len(celdas) != 3:
                continue

            servicio = celdas[0].get_text(strip=True)
            equipo = celdas[1].get_text(strip=True)
            precio = _a_numero(
                celdas[2].get_text(strip=True)
            )

            servicio_raw = f"{servicio} - {equipo}" if equipo else servicio

            resultados.append(
                OfertaDTO(
                    empresa_nombre="BairesCloud",
                    provincia="Buenos Aires",
                    ciudad="Buenos Aires",
                    fuente="https://bairescloud.ar/servicio-tecnico.php",
                    servicio_raw=servicio_raw,
                    precio=precio,
                    moneda="ARS",
                    fecha_relevamiento=fecha_relevamiento,
                )
            )

    return resultados