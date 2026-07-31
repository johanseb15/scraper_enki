from datetime import date

from src.aplicacion.dto.oferta_dto import OfertaDTO


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