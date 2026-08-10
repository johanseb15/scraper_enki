from datetime import date

from src.dominio.comparabilidad import (
    CausaComparabilidad,
    EstadoComparabilidad,
    evaluar_comparabilidad,
)
from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta, PrecioValor
from src.dominio.servicios import ServicioCanonico


def _oferta(
    empresa: str,
    precio,
    *,
    fuente: str = "corpus-real",
    servicio_raw: str = "Soporte tecnico PC",
    modalidad: str | None = "local",
    precio_raw: str | None = "$50.000",
):
    return Oferta(
        empresa=Empresa(
            nombre=empresa,
            provincia="Cordoba",
            ciudad="Cordoba",
            fuente=fuente,
        ),
        servicio=ServicioCanonico.SOPORTE_TECNICO,
        servicio_raw=servicio_raw,
        precio=precio,
        precio_raw=precio_raw,
        modalidad=modalidad,
        moneda=getattr(precio, "moneda", "ARS"),
        fecha_relevamiento=date(2026, 8, 10),
    )


def test_puntual_vs_puntual_real_queda_potencialmente_comparable():
    dmr = _oferta("DMR", PrecioValor(50000, "ARS"))
    reed = _oferta("REED Technology", PrecioValor(52000, "ARS"))

    resultado = evaluar_comparabilidad(dmr, reed)

    assert resultado.estado == EstadoComparabilidad.POTENCIALMENTE_COMPARABLE
    assert resultado.causas == ()


def test_puntual_vs_mensual_no_es_comparable_por_periodicidad():
    intervencion = _oferta("CiroWhite", PrecioValor(50000, "ARS"))
    abono = _oferta(
        "Helpdesk",
        PrecioValor(300000, "ARS", "mensual"),
        precio_raw="$300.000 / mes",
    )

    resultado = evaluar_comparabilidad(intervencion, abono)

    assert resultado.estado == EstadoComparabilidad.NO_COMPARABLE
    assert resultado.causas == (
        CausaComparabilidad.PERIODICIDAD_INCOMPATIBLE,
    )


def test_mensual_vs_mensual_sin_denominador_queda_indeterminado():
    digital = _oferta(
        "Digital",
        PrecioValor(199, "USD", "mensual"),
        fuente="digital.com.ar",
        precio_raw="US$ 199 /mes",
    )
    helpdesk = _oferta(
        "Helpdesk",
        PrecioValor(300000, "ARS", "mensual"),
        precio_raw="$300.000 / mes",
    )

    resultado = evaluar_comparabilidad(digital, helpdesk)

    assert resultado.estado == EstadoComparabilidad.INDETERMINADO
    assert resultado.causas == (
        CausaComparabilidad.UNIDAD_ECONOMICA_DESCONOCIDA,
    )


def test_mismo_periodo_con_scope_material_distinto_no_compara_directo():
    printos = _oferta(
        "PrintOS",
        PrecioValor(150000, "ARS", "mensual"),
        servicio_raw="Abono mensual con equipo, insumos y mantenimiento",
        precio_raw="$150.000 / mes",
    )
    helpdesk = _oferta(
        "Helpdesk",
        PrecioValor(150000, "ARS", "mensual"),
        servicio_raw="Abono mensual de soporte IT",
        precio_raw="$150.000 / mes",
    )

    resultado = evaluar_comparabilidad(printos, helpdesk)

    assert resultado.estado == EstadoComparabilidad.NO_COMPARABLE
    assert resultado.causas == (
        CausaComparabilidad.SCOPE_MATERIAL_DISTINTO,
    )


def test_precio_orientativo_no_se_excluye_pero_deja_advertencia():
    dmr = _oferta(
        "DMR",
        PrecioValor(50000, "ARS"),
        precio_raw="$50.000 orientativo",
    )
    reed = _oferta("REED Technology", PrecioValor(52000, "ARS"))

    resultado = evaluar_comparabilidad(dmr, reed)

    assert resultado.estado == EstadoComparabilidad.POTENCIALMENTE_COMPARABLE
    assert resultado.advertencias == (
        CausaComparabilidad.PRECIO_ORIENTATIVO,
    )


def test_fuente_no_apta_impide_usar_precio_parseable_en_benchmark():
    digital = _oferta(
        "Digital",
        PrecioValor(199, "USD", "mensual"),
        fuente="digital.com.ar",
        precio_raw="US$ 199 /mes",
    )
    helpdesk = _oferta(
        "Helpdesk",
        PrecioValor(300000, "ARS", "mensual"),
        precio_raw="$300.000 / mes",
    )

    resultado = evaluar_comparabilidad(
        digital,
        helpdesk,
        fuentes_no_aptas={"digital.com.ar"},
    )

    assert resultado.estado == EstadoComparabilidad.INDETERMINADO
    assert resultado.causas == (
        CausaComparabilidad.FUENTE_NO_APTA,
    )


def test_ausencia_de_periodo_en_una_observacion_declara_indeterminado():
    reed = _oferta("REED Technology", 52000)
    helpdesk = _oferta(
        "Helpdesk",
        PrecioValor(300000, "ARS", "mensual"),
        precio_raw="$300.000 / mes",
    )

    resultado = evaluar_comparabilidad(reed, helpdesk)

    assert resultado.estado == EstadoComparabilidad.INDETERMINADO
    assert resultado.causas == (
        CausaComparabilidad.PERIODICIDAD_DESCONOCIDA,
    )
