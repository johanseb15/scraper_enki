from datetime import date
from bs4 import BeautifulSoup
from src.modelos.servicio_precio import ServicioPrecio

def _a_numero(texto: str) -> int:
    """
    Convierte textos como '$29.816' o '29816' al entero 29816.
    """
    solo_digitos = "".join(c for c in texto if c.isdigit())
    return int(solo_digitos) if solo_digitos else 0


def extraer_datos(html: str) -> list[dict]:
    """
    Recibe el HTML de una página de precios y devuelve una lista
    de diccionarios, uno por cada fila de la tabla de precios.
    """

    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table")

    if tabla is None:
        return []

    resultados = []

    filas = tabla.find_all("tr")

    for fila in filas[1:]:  # Ignorar encabezados
        celdas = fila.find_all("td")

        if len(celdas) < 4:
            continue

        tipo_arreglo = celdas[0].get_text(strip=True)
        tipo_equipo = celdas[1].get_text(strip=True)
        precio_freelance = _a_numero(celdas[2].get_text(strip=True))
        precio_local = _a_numero(celdas[3].get_text(strip=True))

        resultados.append(
            ServicioPrecio(
                empresa="Vida informatica",
                provincia="",
                ciudad="",
                servicio=tipo_arreglo,
                equipo=tipo_equipo,
                precio_freelance=precio_freelance,
                precio_local=precio_local,
                moneda="ARS",
                fecha_relevamiento=date.today(),
                fuente="",
            )
        )

    return resultados