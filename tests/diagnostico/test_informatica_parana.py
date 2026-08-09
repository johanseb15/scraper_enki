from pathlib import Path

from src.infraestructura.diagnostico.informatica_parana import (
    caracterizar_informatica_parana,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "informatica_parana.html"


def _caracterizacion():
    return caracterizar_informatica_parana(FIXTURE.read_text(encoding="utf-8"))


def test_caracteriza_proveedor_ubicacion_y_cobertura_desde_json_ld():
    resultado = _caracterizacion()

    assert resultado.tipo_proveedor == "LocalBusiness"
    assert resultado.proveedor_raw == "Informática Paraná"
    assert resultado.url == "https://informaticaparana.com.ar/"
    assert resultado.direccion_raw == "Calle 1666, Paraná, Entre Ríos, AR"
    assert resultado.cobertura_raw == (
        "Paraná",
        "Oro Verde",
        "Entre Ríos",
        "Santa Fe",
    )
    assert resultado.moneda_aceptada_raw == "ARS"
    assert resultado.rango_precio_raw == "$$"


def test_offer_catalog_declara_servicios_pero_no_precios():
    resultado = _caracterizacion()

    assert resultado.tipo_catalogo == "OfferCatalog"
    assert resultado.nombre_catalogo_raw == "Servicios"
    assert len(resultado.unidades_estructuradas) == 8
    assert {u.tipo_oferta for u in resultado.unidades_estructuradas} == {"Offer"}
    assert {u.tipo_item for u in resultado.unidades_estructuradas} == {"Service"}
    assert all(u.precio_raw is None for u in resultado.unidades_estructuradas)
    assert all(u.price_specification_raw is None for u in resultado.unidades_estructuradas)
    assert all(u.moneda_raw is None for u in resultado.unidades_estructuradas)
    assert all(u.availability_raw is None for u in resultado.unidades_estructuradas)
    assert all(u.provider_raw is None for u in resultado.unidades_estructuradas)
    assert all(u.area_served_raw == () for u in resultado.unidades_estructuradas)


def test_preserva_corpus_de_nombres_comerciales_sin_crear_ofertas_de_precio():
    resultado = _caracterizacion()

    assert [u.nombre_raw for u in resultado.unidades_estructuradas] == [
        "Servicio técnico de PC y notebooks",
        "Reparación de impresoras",
        "Servicio técnico remoto",
        "Instalación de cámaras de seguridad",
        "Cableados de red",
        "Sistema de abonos para empresas",
        "Venta de insumos y cartuchos",
        "Retiro y entrega a domicilio",
    ]
    assert resultado.cantidad_precios == 0
    assert resultado.cantidad_ofertas_sin_precio == 8


def test_preserva_condiciones_comerciales_visibles_sin_clasificarlas_como_rechazo():
    resultado = _caracterizacion()

    assert resultado.senales_comerciales_raw == (
        "Servicio técnico de PC, notebooks e impresoras. Retiro y entrega a domicilio sin cargo en Paraná y Oro Verde. Diagnóstico siempre sin cargo.",
        "10% OFF en tu primer servicio técnico",
        "Garantía en cada reparación",
    )
    assert resultado.rechazos == ()
