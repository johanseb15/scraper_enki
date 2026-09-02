from datetime import date
from pathlib import Path

from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.infraestructura.scrapers.dmr_parser import (
    extraer_candidatos_dmr,
    extraer_contexto_dmr,
    parsear_ofertas_dmr,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "dmr_mantenimiento.html"
URL = "https://dmrwebdesign.com.ar/mantenimiento.html"


def _html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_caracteriza_temporalidad_editorial_sin_confundirla_con_relevamiento():
    contexto = extraer_contexto_dmr(_html())

    assert contexto.empresa_raw == "DMR Web Design"
    assert contexto.provincia_raw == "Mendoza"
    assert contexto.ciudad_raw == "Mendoza Capital"
    assert contexto.fecha_editorial_raw == "abril 2026"
    assert contexto.alcance_fecha_editorial == "lista_de_precios"
    assert "Precios orientativos actualizados abril 2026" in contexto.textos_temporales_raw
    assert (
        "precio final se confirma después del diagnóstico"
        in contexto.aviso_precio_raw.casefold()
    )


def test_caracteriza_tarjetas_con_evidencia_comercial_raw():
    candidatos = extraer_candidatos_dmr(
        _html(), URL, fecha_relevamiento=date(2026, 8, 9)
    )

    primero = candidatos[0]
    assert len(candidatos) == 3
    assert primero.servicio_raw == "Formateo e instalación de SO sin BackUp"
    assert primero.precio_raw == "$49.700"
    assert primero.precio_interpretado == 49700
    assert primero.semantica_precio == "exacto"
    assert primero.moneda == "ARS"
    assert primero.categoria_raw == "software"
    assert primero.equipos_raw == ("PC", "Notebook")
    assert primero.modalidad_raw == "Freelance / taller"
    assert primero.fecha_editorial_raw == "abril 2026"
    assert primero.fecha_relevamiento == date(2026, 8, 9)


def test_genera_dto_solo_para_precios_exactos_y_preserva_raw():
    rechazos: list[RechazoIngesta] = []

    dtos = parsear_ofertas_dmr(
        _html(), URL, fecha_relevamiento=date(2026, 8, 9), rechazos=rechazos
    )

    assert len(dtos) == 3
    assert rechazos == []
    assert dtos[0].servicio_raw == "Formateo e instalación de SO sin BackUp"
    assert dtos[0].equipo_raw == "PC / Notebook"
    assert dtos[0].precio == 49700
    assert dtos[0].precio_raw == "$49.700"
    assert dtos[0].empresa_nombre == "DMR Web Design"
    assert dtos[0].provincia == "Mendoza"
    assert dtos[0].ciudad == "Mendoza Capital"
    assert dtos[0].fuente == URL
    assert dtos[0].fecha_relevamiento == date(2026, 8, 9)


def test_rechaza_semanticas_no_exactas_de_forma_trazable():
    html = _html().replace("$49.700", "Desde $49.700", 1)
    rechazos: list[RechazoIngesta] = []

    dtos = parsear_ofertas_dmr(
        html, URL, fecha_relevamiento=date(2026, 8, 9), rechazos=rechazos
    )

    assert len(dtos) == 2
    assert len(rechazos) == 1
    assert rechazos[0].fuente == URL
    assert "PRECIO_NO_REPRESENTABLE" in rechazos[0].razon
    assert "Desde $49.700" in rechazos[0].razon


def test_acepta_layout_svc_publicado_sin_perder_evidencia_raw():
    html = """
    <html>
      <body>
        <a class="nav-logo"><span class="dot"></span>DMR/web+it</a>
        <div class="hero-tag">Mendoza Capital · A domicilio y en taller</div>
        <section id="precios">
          <h2>Precios orientativos —<br>abril 2026.</h2>
          <p class="section-sub">
            Referencia de mercado en Mendoza Capital.
            El precio final se confirma después del diagnóstico.
          </p>
          <div class="note">
            Estos son valores de referencia. Siempre se informa el precio final.
          </div>
          <div class="svc" data-cat="software">
            <div>
              <div class="svc-name">Formateo e instalación de SO sin backup</div>
              <div class="svc-tags"><span>PC</span><span>Notebook</span></div>
            </div>
            <div class="svc-price">$49.700</div>
          </div>
          <div class="svc" data-cat="domicilio">
            <div>
              <div class="svc-name">Visita a domicilio x1 hora</div>
              <div class="svc-tags"><span>PC</span><span>Notebook</span></div>
            </div>
            <div class="svc-price">$24.300</div>
          </div>
        </section>
      </body>
    </html>
    """

    candidatos = extraer_candidatos_dmr(
        html,
        URL,
        fecha_relevamiento=date(2026, 9, 2),
    )

    assert len(candidatos) == 2
    assert candidatos[0].categoria_raw == "software"
    assert candidatos[0].servicio_raw == (
        "Formateo e instalación de SO sin backup"
    )
    assert candidatos[0].equipos_raw == ("PC", "Notebook")
    assert candidatos[0].precio_raw == "$49.700"
    assert candidatos[0].precio_interpretado == 49700
    assert candidatos[0].fecha_editorial_raw == "abril 2026"

    ofertas = parsear_ofertas_dmr(
        html,
        URL,
        fecha_relevamiento=date(2026, 9, 2),
    )

    assert len(ofertas) == 2
    assert ofertas[1].servicio_raw == "Visita a domicilio x1 hora"
    assert ofertas[1].equipo_raw == "PC / Notebook"
    assert ofertas[1].precio == 24300
