from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.dominio.servicios import ServicioCanonico


def test_procesador_normaliza_empresa_y_ubicacion_antes_del_dominio():
    dto = OfertaDTO(
        empresa="VIDA INFORMATICA S.R.L.",
        provincia="Cordoba",
        ciudad="Cba.",
        servicio="Eliminación de virus y malware",
        precio=15000,
        moneda="ARS",
        fuente="https://soportetotal.com"
    )

    procesador = ProcesadorOfertas()
    oferta = procesador.crear_oferta(dto)

    assert oferta is not None
    assert oferta.empresa.nombre == "Vida Informatica"
    assert oferta.empresa.provincia == "Córdoba"
    assert oferta.empresa.ciudad == "Córdoba"


def test_factory_normaliza_servicio_y_precio_en_unico_paso():
    dto = OfertaDTO(
        empresa="Empresa X",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Eliminación de malware",
        precio_raw="$ 25.000 USD",
        moneda="ARS",
        fuente="https://ejemplo.com",
    )

    procesador = ProcesadorOfertas()
    oferta = procesador.crear_oferta(dto)

    assert oferta is not None
    assert oferta.servicio == ServicioCanonico.MALWARE
    assert oferta.precio.valor == 25000
    assert oferta.precio.moneda == "USD"


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


def test_procesador_acepta_fecha_relevamiento_en_crear_oferta():

    dto = OfertaDTO(
        empresa="Empresa X",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Eliminación de malware",
        precio=15000,
        moneda="ARS",
        fuente="https://empresa.com",
    )

    procesador = ProcesadorOfertas()

    oferta = procesador.crear_oferta(dto, fecha_relevamiento="2026-01-01")

    assert oferta is not None
    assert oferta.fecha_relevamiento is None


def test_procesador_maneja_dto_incompleto_sin_romper_el_pipeline():

    dto = OfertaDTO(
        empresa="Empresa X",
        provincia="",
        ciudad="",
        servicio="",
        precio=None,
        moneda="ARS",
        fuente="https://empresa.com",
    )

    procesador = ProcesadorOfertas()

    oferta = procesador.crear_oferta(dto)

    assert oferta is None