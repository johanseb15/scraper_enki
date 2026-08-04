from datetime import date
from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.normalizadores.normalizador_servicios import NormalizadorServicios
from src.dominio.servicios import ServicioCanonico


def _a_numero(texto: str) -> int:
    """
    Convierte textos como '$29.816' o '29816' al entero 29816.
    """
    solo_digitos = "".join(c for c in texto if c.isdigit())
    return int(solo_digitos) if solo_digitos else 0


def extraer_datos(
    html: str, normalizador: NormalizadorServicios | None = None
) -> list[OfertaDTO]:
    """
    Recibe HTML de una página de precios y devuelve ofertas de aplicación.
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

        servicio_canonico = normalizador.normalizar(tipo_arreglo)
        servicio_raw = (
            f"{tipo_arreglo} - {tipo_equipo}" if tipo_equipo else tipo_arreglo
        )

        resultados.append(
            OfertaDTO(
                empresa_nombre="Vida informatica",
                provincia="Córdoba",
                ciudad="Córdoba",
                fuente="https://vidainformatica.com.ar/listado-de-precios-zona-1/",
                servicio_raw=servicio_canonico.value if hasattr(servicio_canonico, "value") else servicio_raw,
                precio=precio_freelance,
                moneda="ARS",
                fecha_relevamiento=date.today(),
            )
        )

    return resultados
