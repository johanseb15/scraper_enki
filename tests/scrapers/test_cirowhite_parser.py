from datetime import date

import pytest

from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.infraestructura.scrapers.cirowhite_parser import (
    ClasificacionPrecio,
    clasificar_precio_cirowhite,
    extraer_candidatos_cirowhite,
    parsear_ofertas_cirowhite,
)


HTML_CARACTERIZACION = """
<html>
  <head><title>CiroWhite Informática</title></head>
  <body>
    <div id="tab-imp" class="tab-content active">
      <div class="pc">
        <div class="pc-name">Diagnóstico</div>
        <div class="pc-price">$5.000</div>
        <div class="pc-note">Se bonifica si realizás el trabajo</div>
        <ul class="pc-feats"><li>Evaluación completa</li></ul>
      </div>
      <div class="pc">
        <div class="pc-name">Mantenimiento Preventivo</div>
        <div class="pc-price">Desde $45.000</div>
        <div class="pc-note">Inkjet $45-60k · Láser $55-75k</div>
        <ul class="pc-feats"><li>Retiro y entrega incluidos</li></ul>
      </div>
    </div>
    <div id="tab-pc" class="tab-content">
      <div class="pc">
        <div class="pc-name">Armado de PC</div>
        <div class="pc-price">$40.000–$70.000</div>
        <div class="pc-note">Gamer o profesional</div>
        <ul class="pc-feats">
          <li>Armado con tus componentes</li>
          <li>Instalación componentes: $25.000</li>
        </ul>
      </div>
    </div>
    <footer>
      <div class="ft-brand-name">CiroWhite Informática</div>
      <div class="ft-brand-sub">Servicio técnico a domicilio · Tucumán, Argentina</div>
      <p>San Miguel de Tucumán</p>
    </footer>
  </body>
</html>
"""


@pytest.mark.parametrize(
    ("precio_raw", "clasificacion", "valor"),
    [
        ("$5.000", ClasificacionPrecio.NUMERICO_INEQUIVOCO, 5000),
        ("$20.000", ClasificacionPrecio.NUMERICO_INEQUIVOCO, 20000),
        ("$35.000", ClasificacionPrecio.NUMERICO_INEQUIVOCO, 35000),
        ("$45.000", ClasificacionPrecio.NUMERICO_INEQUIVOCO, 45000),
        ("$60.000", ClasificacionPrecio.NUMERICO_INEQUIVOCO, 60000),
        ("$45", ClasificacionPrecio.NUMERICO_POTENCIALMENTE_AMBIGUO, None),
        ("$55", ClasificacionPrecio.NUMERICO_POTENCIALMENTE_AMBIGUO, None),
        ("", ClasificacionPrecio.SIN_PRECIO, None),
        ("Consultar", ClasificacionPrecio.TEXTO_ESPECIAL, None),
    ],
)
def test_clasifica_literal_sin_inventar_miles(precio_raw, clasificacion, valor):
    resultado = clasificar_precio_cirowhite(precio_raw)

    assert resultado.raw == precio_raw
    assert resultado.clasificacion is clasificacion
    assert resultado.valor_numerico == valor


def test_caracteriza_tarjetas_y_preserva_contexto_raw():
    candidatos = extraer_candidatos_cirowhite(
        HTML_CARACTERIZACION,
        url_fuente="https://cirowhiteinformatica.com.ar/landing/",
        fecha_relevamiento=date(2026, 8, 8),
    )

    mantenimiento = next(c for c in candidatos if c.servicio_raw == "Mantenimiento Preventivo")
    armado = next(c for c in candidatos if c.servicio_raw == "Armado de PC")
    instalacion = next(c for c in candidatos if c.servicio_raw == "Instalación componentes")

    assert mantenimiento.categoria_raw == "Impresoras"
    assert mantenimiento.precio.raw == "Desde $45.000"
    assert mantenimiento.precio.clasificacion is ClasificacionPrecio.TEXTO_ESPECIAL
    assert mantenimiento.precio.valor_numerico == 45000
    assert mantenimiento.precio.desde is True
    assert mantenimiento.nota_raw == "Inkjet $45-60k · Láser $55-75k"
    assert mantenimiento.prestaciones_raw == ("Retiro y entrega incluidos",)
    assert mantenimiento.empresa_raw == "CiroWhite Informática"
    assert mantenimiento.provincia_raw == "Tucumán"
    assert mantenimiento.ciudad_raw == "San Miguel de Tucumán"
    assert mantenimiento.fecha_relevamiento == date(2026, 8, 8)

    assert armado.precio.precio_minimo == 40000
    assert armado.precio.precio_maximo == 70000
    assert instalacion.categoria_raw == "PC Escritorio"
    assert instalacion.precio.raw == "$25.000"
    assert instalacion.precio.valor_numerico == 25000


def test_caracteriza_tarjeta_general_sin_confundirla_con_precio_exacto():
    html = """
      <section class="services">
        <div class="scard">
          <div class="sc-title">Celulares</div>
          <div class="sc-desc">Reparación de smartphones de todas las marcas.</div>
          <ul class="sc-list"><li>Cambio de pantalla / módulo</li></ul>
          <span class="sc-price">Desde $20.000 + repuesto</span>
        </div>
      </section>
      <footer><div class="ft-brand-name">CiroWhite Informática</div>
      <p>San Miguel de Tucumán, Tucumán · Servicio a domicilio</p></footer>
    """

    candidato = extraer_candidatos_cirowhite(
        html,
        url_fuente="https://cirowhiteinformatica.com.ar/landing/",
        fecha_relevamiento=date(2026, 8, 8),
    )[0]

    assert candidato.categoria_raw == "Servicios"
    assert candidato.servicio_raw == "Celulares"
    assert candidato.descripcion_raw == "Reparación de smartphones de todas las marcas."
    assert candidato.prestaciones_raw == ("Cambio de pantalla / módulo",)
    assert candidato.precio.raw == "Desde $20.000 + repuesto"
    assert candidato.precio.clasificacion is ClasificacionPrecio.TEXTO_ESPECIAL
    assert candidato.precio.valor_numerico == 20000


def test_genera_dto_solo_para_precios_inequivocos_y_rechaza_el_resto():
    rechazos: list[RechazoIngesta] = []

    dtos = parsear_ofertas_cirowhite(
        HTML_CARACTERIZACION,
        url_fuente="https://cirowhiteinformatica.com.ar/landing/",
        fecha_relevamiento=date(2026, 8, 8),
        rechazos=rechazos,
    )

    assert [(dto.servicio_raw, dto.precio, dto.precio_raw) for dto in dtos] == [
        ("Diagnóstico", 5000, "$5.000"),
        ("Instalación componentes", 25000, "$25.000"),
    ]
    assert all(dto.empresa_nombre == "CiroWhite Informática" for dto in dtos)
    assert all(dto.provincia == "Tucumán" for dto in dtos)
    assert all(dto.ciudad == "San Miguel de Tucumán" for dto in dtos)
    assert all(dto.fuente == "https://cirowhiteinformatica.com.ar/landing/" for dto in dtos)
    assert all(dto.fecha_relevamiento == date(2026, 8, 8) for dto in dtos)
    assert {rechazo.razon for rechazo in rechazos} == {
        "Mantenimiento Preventivo: precio texto_especial 'Desde $45.000'",
        "Armado de PC: precio texto_especial '$40.000–$70.000'",
    }
