from datetime import date

from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta, PrecioValor
from src.dominio.servicios import ServicioCanonico
from src.estadisticas import calcular_precio_promedio


def _oferta(empresa: str, precio):
    return Oferta(
        empresa=Empresa(
            nombre=empresa,
            provincia="Cordoba",
            ciudad="Cordoba",
            fuente="corpus-real",
        ),
        servicio=ServicioCanonico.SOPORTE_TECNICO,
        servicio_raw="Soporte tecnico PC",
        precio=precio,
        moneda=getattr(precio, "moneda", "ARS"),
        fecha_relevamiento=date(2026, 8, 10),
    )


def test_estadisticas_no_promedian_puntual_con_mensualidad_conocida():
    puntual = _oferta("CiroWhite", PrecioValor(50000, "ARS"))
    mensual = _oferta("Helpdesk", PrecioValor(300000, "ARS", "mensual"))

    assert calcular_precio_promedio([puntual, mensual]) == 50000
