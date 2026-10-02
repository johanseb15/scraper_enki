from src.normalizadores.normalizador_precios import NormalizadorPrecios
from decimal import Decimal


def test_centavos_decimal_y_texto_original():
    resultado = NormalizadorPrecios.normalizar("$1.299,50")
    assert resultado.valor == Decimal("1299.50")
    assert isinstance(resultado.valor, Decimal)
    assert resultado.raw == "$1.299,50"


def test_normaliza_precio_argentino_con_simbolo_y_separadores():
    precio_crudo = "$ 1.250.000 ARS"

    resultado = NormalizadorPrecios.normalizar(precio_crudo)

    assert resultado.valor == 1250000
    assert resultado.moneda == "ARS"


def test_normaliza_precio_mensual():
    precio_crudo = "USD 250 / mes"

    resultado = NormalizadorPrecios.normalizar(precio_crudo)

    assert resultado.valor == 250
    assert resultado.moneda == "USD"
    assert resultado.periodo == "mensual"


def test_normaliza_marcador_u_dolar_s_como_usd():
    resultado = NormalizadorPrecios.normalizar("U$S 250")

    assert resultado.moneda == "USD"
