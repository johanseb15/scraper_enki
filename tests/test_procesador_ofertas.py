import pytest
from datetime import date
from src.dominio.servicios import ServicioCanonico
from src.dominio.oferta import Oferta
from src.aplicacion.dtos import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas


def test_procesador_crea_oferta_valida_desde_dto():
    # Arrange: Usando el DTO tipado y seguro
    dto = OfertaDTO(
        empresa="Soporte Total Córdoba",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Eliminación de virus y malware",
        precio=15000,
        moneda="ARS",
        fuente="https://soportetotal.com"
    )
    
    procesador = ProcesadorOfertas()

    # Act
    oferta = procesador.crear_oferta(dto, fecha_relevamiento=date(2026, 7, 30))

    # Assert
    assert isinstance(oferta, Oferta)
    assert oferta.empresa.nombre == "Soporte Total Córdoba"
    assert oferta.empresa.provincia == "Córdoba"
    assert oferta.servicio == ServicioCanonico.MALWARE
    assert oferta.precio == 15000
    assert oferta.moneda == "ARS"


def test_procesador_maneja_servicio_desconocido_con_resiliencia():
    # Arrange: Servicio no catalogado
    dto = OfertaDTO(
        empresa="Tecno Service",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Servicio cuántico inexistente",
        precio=50000,
        moneda="ARS",
        fuente="https://tecnoservice.com"
    )
    
    procesador = ProcesadorOfertas()

    # Act
    oferta = procesador.crear_oferta(dto, fecha_relevamiento=date(2026, 7, 30))

    # Assert: El ETL no rompe, procesa la oferta y la clasifica de manera segura
    assert isinstance(oferta, Oferta)
    if hasattr(ServicioCanonico, "DESCONOCIDO"):
        assert oferta.servicio == ServicioCanonico.DESCONOCIDO