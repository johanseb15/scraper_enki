from src.dominio.oferta import PrecioValor
from src.dominio.servicios import ServicioCanonico
from src.normalizadores.normalizador_servicios import NormalizadorServicios


def test_normalizador_descarta_servicio_desconocido():
    normalizador = NormalizadorServicios()

    resultado = normalizador.normalizar("Producto Sin Relación Comercial 123")

    assert resultado is ServicioCanonico.DESCONOCIDO


def test_contrato_precio_y_monto():
    precio = PrecioValor(35000, moneda="ARS")

    assert precio.valor == 35000
    assert precio.moneda == "ARS"
    assert precio == 35000
