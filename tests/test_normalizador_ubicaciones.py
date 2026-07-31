from src.dominio.normalizador_ubicaciones import NormalizadorUbicaciones


def test_normalizador_ubicacion_unifica_variantes_de_ciudad():
    normalizador = NormalizadorUbicaciones()

    resultado = normalizador.normalizar(
        provincia="Cordoba",
        ciudad="Cba."
    )

    assert resultado.provincia == "Córdoba"
    assert resultado.ciudad == "Córdoba"