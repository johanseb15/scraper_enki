from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.oferta_factory import OfertaFactory
from src.dominio.oferta import PrecioValor
from src.dominio.servicios import ServicioCanonico


class NormalizadorFalso:
    def normalizar(self, texto):
        return None


def test_crear_desde_dto_devuelve_none_para_servicio_desconocido():
    dto = OfertaDTO(
        empresa="Empresa X",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Servicio no soportado",
        precio=15000,
        moneda="ARS",
        fuente="https://ejemplo.com",
    )

    factory = OfertaFactory(normalizador=NormalizadorFalso())

    oferta = factory.crear_desde_dto(dto)

    assert oferta is None


def test_crear_desde_dto_normaliza_precio_crudo_cuando_no_hay_precio():
    dto = OfertaDTO(
        empresa="Empresa Y",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Eliminación de malware",
        precio=None,
        moneda="ARS",
        precio_raw="$ 25.000 USD",
        fuente="https://ejemplo.com",
    )

    factory = OfertaFactory()

    oferta = factory.crear_desde_dto(dto)

    assert oferta is not None
    assert oferta.precio.valor == 25000
    assert oferta.precio.moneda == "USD"


def test_crear_desde_dto_respeta_precio_valor_cuando_llega_como_objeto():
    dto = OfertaDTO(
        empresa="Empresa Z",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Eliminación de malware",
        precio=PrecioValor(18000, "USD", "mensual"),
        moneda="ARS",
        fuente="https://ejemplo.com",
    )

    factory = OfertaFactory()

    oferta = factory.crear_desde_dto(dto)

    assert oferta is not None
    assert oferta.precio.valor == 18000
    assert oferta.precio.moneda == "USD"
    assert oferta.precio.periodo == "mensual"
