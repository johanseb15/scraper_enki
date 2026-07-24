from datetime import date
from pathlib import Path

from src.scrapers.bairescloud import extraer_precios_bairescloud
from src.modelos.servicio_precio import ServicioPrecio


def test_bairescloud_extrae_servicios_desde_html():
    html = Path(
        "tests/fixtures/bairescloud.html"
    ).read_text(encoding="utf-8")

    datos = extraer_precios_bairescloud(
        html=html,
        fecha_relevamiento=date(2026, 2, 1),
    )

    assert len(datos) >= 20

    primer_servicio = datos[0]

    assert isinstance(primer_servicio, ServicioPrecio)
    assert primer_servicio.empresa == "BairesCloud"
    assert primer_servicio.servicio == "Diagnostico / Revisión"
    assert primer_servicio.equipo == "PC-Notebook-AIO"
    assert primer_servicio.precio_freelance == 30000
    assert primer_servicio.moneda == "ARS"
    assert primer_servicio.fuente == "https://bairescloud.ar/servicio-tecnico.php"

def test_bairescloud_acepta_precio_con_texto_adicional():
    html = """
    <table>
        <thead>
            <tr>
                <th>Servicio</th>
                <th>Equipo</th>
                <th>Precio</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Servicio mensual</td>
                <td>PC</td>
                <td>$38.000,00 x MES</td>
            </tr>
        </tbody>
    </table>
    """

    datos = extraer_precios_bairescloud(
        html=html,
        fecha_relevamiento=date(2026, 2, 1),
    )

    assert len(datos) == 1
    assert datos[0].precio_freelance == 38000