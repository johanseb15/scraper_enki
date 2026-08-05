from datetime import date
from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO


def _a_numero(texto: str) -> int:
    """Convierte textos como '$29.816' o '29816' al entero 29816."""
    solo_digitos = "".join(c for c in texto if c.isdigit())
    return int(solo_digitos) if solo_digitos else 0


def extraer_datos_vida_informatica(
    html: str,
    url_fuente: str = "https://vidainformatica.com.ar/listado-de-precios-zona-1/",
    fecha_relevamiento: date | None = None,
) -> list[OfertaDTO]:
    """Parsea el HTML de la tabla de precios de Vida Informática directamente a OfertaDTO."""
    if fecha_relevamiento is None:
        fecha_relevamiento = date.today()

    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table")

    if tabla is None:
        return []

    resultados: list[OfertaDTO] = []
    filas = tabla.find_all("tr")

    for fila in filas[1:]:
        celdas = fila.find_all("td")

        if len(celdas) < 4:
            continue

        tipo_arreglo = celdas[0].get_text(strip=True)
        tipo_equipo = celdas[1].get_text(strip=True)

        precio_freelance = _a_numero(celdas[2].get_text(strip=True))

        if precio_freelance <= 0:
            continue

        servicio_raw = (
            f"{tipo_arreglo} - {tipo_equipo}" if tipo_equipo else tipo_arreglo
        )

        resultados.append(
            OfertaDTO(
                empresa_nombre="Vida Informatica",
                provincia="Córdoba",
                ciudad="Córdoba",
                fuente=url_fuente,
                servicio_raw=servicio_raw,
                precio=precio_freelance,
                moneda="ARS",
                fecha_relevamiento=fecha_relevamiento,
            )
        )

    return resultados