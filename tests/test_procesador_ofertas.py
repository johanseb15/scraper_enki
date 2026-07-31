from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas


def test_procesador_crea_oferta_valida_desde_dto():

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

    oferta = procesador.crear_oferta(dto)

    assert oferta is not None
    assert oferta.empresa.nombre == "Soporte Total Córdoba"



def test_procesador_maneja_servicio_desconocido_con_resiliencia():

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

    oferta = procesador.crear_oferta(dto)

    assert oferta is None or oferta.servicio is not None



def test_procesador_normaliza_precio_crudo_del_dto():

    dto = OfertaDTO(
        empresa="Vida Informatica",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Eliminación de malware",
        precio_raw="$ 25.000 ARS",
        moneda="ARS",
        fuente="https://vidainformatica.com"
    )

    procesador = ProcesadorOfertas()

    oferta = procesador.crear_oferta(dto)

    assert oferta.precio.valor == 25000



def test_procesador_normaliza_ubicacion_del_dto():

    dto = OfertaDTO(
        empresa="Servicio Córdoba",
        provincia="Cordoba",
        ciudad="Cba.",
        servicio="Eliminación de malware",
        precio=15000,
        moneda="ARS",
        fuente="https://servicio.com"
    )

    procesador = ProcesadorOfertas()

    oferta = procesador.crear_oferta(dto)

    assert oferta.empresa.provincia == "Córdoba"
    assert oferta.empresa.ciudad == "Córdoba"



def test_procesador_normaliza_nombre_empresa_del_dto():

    dto = OfertaDTO(
        empresa="VIDA INFORMATICA S.R.L.",
        provincia="Cordoba",
        ciudad="Cba.",
        servicio="Eliminación de malware",
        precio=15000,
        moneda="ARS",
        fuente="https://vida.com"
    )

    procesador = ProcesadorOfertas()

    oferta = procesador.crear_oferta(dto)

    assert oferta.empresa.nombre == "Vida Informatica"