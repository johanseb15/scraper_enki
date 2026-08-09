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
