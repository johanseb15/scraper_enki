from datetime import date
from bs4 import BeautifulSoup

from src.dominio.normalizador_servicios import NormalizadorServicios
from src.dominio.servicios import ServicioCanonico
from src.modelos.servicio_precio import ServicioPrecio


def _a_numero(texto: str) -> int:
    """
    Convierte textos como '$29.816' o '29816' al entero 29816.
    """
    solo_digitos = "".join(c for c in texto if c.isdigit())
    return int(solo_digitos) if solo_digitos else 0


def extraer_datos(
    html: str, normalizador: NormalizadorServicios | None = None
) -> list[ServicioPrecio]:
    """
    Recibe HTML de una página de precios y devuelve servicios normalizados.
    """
    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table")

    if tabla is None:
        return []

    if normalizador is None:
        normalizador = NormalizadorServicios()

    resultados = []
    filas = tabla.find_all("tr")

    for fila in filas[1:]:
        celdas = fila.find_all("td")

        if len(celdas) < 4:
            continue

        tipo_arreglo = celdas[0].get_text(strip=True)
        tipo_equipo = celdas[1].get_text(strip=True)

        # Se normaliza la descripción del servicio a su Enum canónico o texto limpio
        servicio_normalizado = normalizador.normalizar(tipo_arreglo)

        precio_freelance = _a_numero(celdas[2].get_text(strip=True))
        precio_local = _a_numero(celdas[3].get_text(strip=True))

        resultados.append(
            ServicioPrecio(
                empresa="Vida informatica",
                provincia="Córdoba",
                ciudad="Córdoba",
                servicio=servicio_normalizado,
                equipo=tipo_equipo,
                precio_freelance=precio_freelance,
                precio_local=precio_local,
                moneda="ARS",
                fecha_relevamiento=date.today(),
                fuente="https://vidainformatica.com.ar/listado-de-precios-zona-1/",
            )
        )

    return resultados