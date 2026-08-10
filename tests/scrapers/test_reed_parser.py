from datetime import date
from pathlib import Path

import pytest

from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.infraestructura.scrapers.reed_parser import (
    SemanticaPrecioReed,
    clasificar_precio_reed,
    extraer_candidatos_reed,
    extraer_contexto_reed,
    parsear_ofertas_reed,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "reed_reparacion_pc.html"
URL = "https://www.reed.ar/servicio-tecnico/7137-reparacion-de-pc.html"


def _html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("raw", "semantica", "valor"),
    [
        ("$63.600", SemanticaPrecioReed.EXACTO, 63600),
        ("$ 0", SemanticaPrecioReed.CERO, None),
        ("Desde $63.600", SemanticaPrecioReed.DESDE, None),
        ("$50.000 - $70.000", SemanticaPrecioReed.RANGO, None),
        ("Consultar", SemanticaPrecioReed.CONSULTAR, None),
        ("", SemanticaPrecioReed.AUSENCIA, None),
        ("$45", SemanticaPrecioReed.AMBIGUO, None),
        ("Precio sujeto a diagnóstico", SemanticaPrecioReed.OTRO, None),
    ],
)
def test_clasifica_semantica_sin_inventar_precio(raw, semantica, valor):
    resultado = clasificar_precio_reed(raw)

    assert resultado.raw == raw
    assert resultado.semantica is semantica
    assert resultado.valor_interpretado == valor


def test_caracteriza_producto_y_precio_cero_con_evidencia():
    contexto = extraer_contexto_reed(_html(), URL)

    assert contexto.empresa_raw == "REED TECHNOLOGY"
    assert contexto.provincia_raw == "Córdoba"
    assert contexto.ciudad_raw == "Córdoba"
    assert contexto.categoria_raw == "SERVICIO TECNICO"
    assert contexto.producto_raw == "Reparación de Pc y Notebooks"
    assert contexto.sku_raw == "04265"
    assert contexto.precio_producto_raw == "$ 0"
    assert contexto.precio_producto_semantica is SemanticaPrecioReed.CERO
    assert contexto.moneda_raw == "ARS"
    assert contexto.availability_raw == "https://schema.org/InStock"
    assert contexto.iva_incluido_raw == "Los precios INCLUYEN IVA"
    assert contexto.url_origen == URL
    assert contexto.vigencia_raw == ""


def test_caracteriza_los_doce_servicios_y_preserva_su_contexto_literal():
    candidatos = extraer_candidatos_reed(
        _html(), URL, fecha_relevamiento=date(2026, 8, 9)
    )

    assert len(candidatos) == 13
    contenedor = candidatos[0]
    primero = candidatos[1]
    bisagra = next(c for c in candidatos if c.precio.raw == "$114.400")

    assert contenedor.tipo_candidato == "producto_contenedor"
    assert contenedor.precio.semantica is SemanticaPrecioReed.CERO
    assert contenedor.servicio_raw == "Reparación de Pc y Notebooks"

    assert primero.tipo_candidato == "servicio_descripto"
    assert primero.servicio_raw == (
        "Formateo con backup hasta 150GB (+$18150 por prog diseño)"
    )
    assert primero.descripcion_raw == (
        "Formateo con backup hasta 150GB (+$18150 por prog diseño) $63.600"
    )
    assert primero.precio.raw == "$63.600"
    assert primero.precio.valor_interpretado == 63600
    assert primero.precio.semantica is SemanticaPrecioReed.EXACTO
    assert primero.empresa_raw == "REED TECHNOLOGY"
    assert primero.provincia_raw == "Córdoba"
    assert primero.ciudad_raw == "Córdoba"
    assert primero.categoria_raw == "SERVICIO TECNICO"
    assert primero.modalidad_raw == ""
    assert primero.fecha_relevamiento == date(2026, 8, 9)

    assert bisagra.descripcion_raw.endswith(
        "$114.400. Incluye limpieza sistema ventilación."
    )
    assert bisagra.servicio_raw == "Reparación de Bisagras POR LADO"


def test_genera_dto_para_precios_exactos_y_rechaza_el_cero_trazablemente():
    rechazos: list[RechazoIngesta] = []

    dtos = parsear_ofertas_reed(
        _html(),
        URL,
        fecha_relevamiento=date(2026, 8, 9),
        rechazos=rechazos,
    )

    assert len(dtos) == 12
    assert dtos[0].servicio_raw == (
        "Formateo con backup hasta 150GB (+$18150 por prog diseño)"
    )
    assert dtos[0].equipo_raw == "Reparación de Pc y Notebooks"
    assert dtos[0].precio == 63600
    assert dtos[0].precio_raw == "$63.600"
    assert dtos[0].empresa_nombre == "REED TECHNOLOGY"
    assert dtos[0].provincia == "Córdoba"
    assert dtos[0].ciudad == "Córdoba"
    assert dtos[0].fuente == URL
    assert dtos[0].fecha_relevamiento == date(2026, 8, 9)
    assert len(rechazos) == 1
    assert rechazos[0].fuente == URL
    assert "PRECIO_CERO_LITERAL" in rechazos[0].razon
    assert "producto_contenedor" in rechazos[0].razon
    assert "$ 0" in rechazos[0].razon
