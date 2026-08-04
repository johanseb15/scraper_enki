from datetime import date

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.normalizadores.normalizador_ofertas import NormalizadorOfertas


def test_normalizador_convierte_dto_crudo_en_oferta_de_dominio():
    dto = OfertaDTO(
        empresa_nombre="VIDA INFORMATICA SRL",
        provincia="Buenos Aires",
        ciudad="Buenos Aires",
        fuente="test",
        servicio_raw="Instalacion Windows 11",
        precio_raw="$ 35.000",
        moneda="ARS",
        fecha_relevamiento=date.today(),
    )

    oferta = NormalizadorOfertas().normalizar(dto)

    assert oferta.empresa.nombre == "Vida Informatica"
    assert oferta.precio == 35000
    assert oferta.servicio is not None


def test_normalizador_no_rompe_con_servicio_desconocido():
    dto = OfertaDTO(
        empresa_nombre="Empresa Nueva",
        servicio_raw="Servicio inexistente 999",
        precio_raw="$ 10000",
    )

    oferta = NormalizadorOfertas().normalizar(dto)

    assert oferta is None