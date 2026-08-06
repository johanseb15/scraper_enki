import pytest
from src.normalizadores.normalizador_servicios import NormalizadorServicios, ServicioCanonico


def test_normaliza_texto_conocido_usando_catalogo():
    normalizador = NormalizadorServicios()

    # Debe mapear según las reglas del normalizador
    resultado = normalizador.normalizar("Mantenimiento preventivo de equipo")

    assert resultado == ServicioCanonico.MANTENIMIENTO


def test_retorna_otro_cuando_no_coincide_con_catalogo():
    normalizador = NormalizadorServicios()

    resultado = normalizador.normalizar("Texto completamente irrelevante 12345")

    assert resultado == ServicioCanonico.DESCONOCIDO