from datetime import date

from src.infraestructura.scrapers.vida_informatica_parser import (
    extraer_datos_vida_informatica,
)


def test_extraer_una_fila_sin_perder_sus_precios_originales():
    html = """
    <table>
      <tr>
        <th>Servicio</th>
        <th>Equipo</th>
        <th>Freelance</th>
        <th>Local</th>
      </tr>
      <tr>
        <td>Eliminación de virus y malware</td>
        <td>PC</td>
        <td>$ 15.000</td>
        <td>$ 20.000</td>
      </tr>
    </table>
    """

    (dto,) = extraer_datos_vida_informatica(
        html,
        url_fuente="Vida Informática",
        fecha_relevamiento=date(2026, 8, 7),
    )

    campos_esperados = {
        "servicio_raw": "Eliminación de virus y malware",
        "equipo_raw": "PC",
        "precio_freelance_raw": "$ 15.000",
        "precio_local_raw": "$ 20.000",
        "fuente": "Vida Informática",
        "fecha_relevamiento": date(2026, 8, 7),
    }
    campos_obtenidos = {
        campo: getattr(dto, campo, "<campo ausente>")
        for campo in campos_esperados
    }

    assert campos_obtenidos == campos_esperados
