from datetime import date
from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta


def _a_numero(texto: str) -> int:
    """Convierte textos como '$29.816' o '29816' al entero 29816."""
    solo_digitos = "".join(c for c in texto if c.isdigit())
    return int(solo_digitos) if solo_digitos else 0


def extraer_datos_vida_informatica(
    html: str,
    url_fuente: str = "https://vidainformatica.com.ar/listado-de-precios-zona-1/",
    fecha_relevamiento: date | None = None,
    rechazos: list[RechazoIngesta] | None = None,
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

        precio_freelance_raw = celdas[2].get_text(strip=True)
        precio_local_raw = celdas[3].get_text(strip=True)
        precio_freelance = _a_numero(precio_freelance_raw)
        precio_local = _a_numero(precio_local_raw)

        if not tipo_arreglo:
            if rechazos is not None:
                rechazos.append(
                    RechazoIngesta(
                        fuente=url_fuente,
                        razon="sin servicio",
                    )
                )
            continue

        if precio_freelance <= 0 and precio_local <= 0:
            if rechazos is not None:
                rechazos.append(
                    RechazoIngesta(
                        fuente=url_fuente,
                        razon="sin ningún precio válido",
                    )
                )
            continue

        precio = precio_freelance if precio_freelance > 0 else precio_local

        resultados.append(
            OfertaDTO(
                empresa_nombre="Vida Informatica",
                provincia="Córdoba",
                ciudad="Córdoba",
                fuente=url_fuente,
                servicio_raw=tipo_arreglo,
                equipo_raw=tipo_equipo,
                precio=precio,
                precio_freelance_raw=precio_freelance_raw,
                precio_local_raw=precio_local_raw,
                moneda="ARS",
                fecha_relevamiento=fecha_relevamiento,
            )
        )

    return resultados
