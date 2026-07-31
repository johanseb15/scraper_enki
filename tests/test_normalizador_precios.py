from src.normalizacion.normalizador_precios import NormalizadorPrecios


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