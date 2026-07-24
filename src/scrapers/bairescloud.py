from datetime import date
import re

from bs4 import BeautifulSoup

from src.modelos.servicio_precio import ServicioPrecio

from src.downloader import descargar_html

class BairesCloudScraper:

    URL = "https://bairescloud.ar/servicio-tecnico.php"

    def obtener_servicios(self) -> list[ServicioPrecio]:
        html = descargar_html(self.URL)

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
) -> list[ServicioPrecio]:
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

            resultados.append(
                ServicioPrecio(
                    empresa="BairesCloud",
                    provincia="Buenos Aires",
                    ciudad="Buenos Aires",
                    servicio=servicio,
                    equipo=equipo,
                    precio_freelance=precio,
                    precio_local=precio,
                    moneda="ARS",
                    fecha_relevamiento=fecha_relevamiento,
                    fuente=(
                        "https://bairescloud.ar/"
                        "servicio-tecnico.php"
                    ),
                )
            )

    return resultados