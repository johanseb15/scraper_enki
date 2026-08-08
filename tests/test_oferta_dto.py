from datetime import date

import importlib
import pathlib

from src.aplicacion.dto.oferta_dto import OfertaDTO


def test_pipeline_usa_unico_modulo_oficial_de_ofertadto():
    modulos_alternativos = [
        "src.modelos.oferta_dto",
        "src.aplicacion.dtos",
    ]

    for nombre_modulo in modulos_alternativos:
        try:
            modulo = importlib.import_module(nombre_modulo)
        except ModuleNotFoundError:
            continue

        oferta_dto_alternativa = getattr(modulo, "OfertaDTO", None)

        if oferta_dto_alternativa is not None:
            assert oferta_dto_alternativa is OfertaDTO


def test_oferta_dto_puede_transportar_precio_crudo():

    dto = OfertaDTO(
        empresa_nombre="Vida Informatica",
        provincia="Cordoba",
        ciudad="Cordoba",
        fuente="web",
        servicio_raw="Formateo",
        precio_raw="$ 25.000 ARS",
        fecha_relevamiento=date.today(),
    )

    assert dto.precio_raw == "$ 25.000 ARS"


def test_oferta_dto_admite_campos_legacy_y_propiedades_compatibles():

    dto = OfertaDTO(
        empresa="Empresa Legacy",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Eliminación de malware",
        precio=15000,
        moneda="ARS",
        fuente="web",
    )

    assert dto.empresa_nombre == "Empresa Legacy"
    assert dto.servicio_raw == "Eliminación de malware"
    assert dto.empresa == "Empresa Legacy"
    assert dto.servicio == "Eliminación de malware"


def test_oferta_dto_permite_valores_none_y_por_defecto():

    dto = OfertaDTO(
        empresa_nombre="Empresa X",
        provincia="Córdoba",
        ciudad="Córdoba",
        fuente="web",
        servicio_raw="Formateo",
    )

    assert dto.precio is None
    assert dto.moneda == "ARS"
    assert dto.precio_raw is None
    assert dto.fecha_relevamiento is None
