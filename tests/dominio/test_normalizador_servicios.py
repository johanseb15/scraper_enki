import pytest
from src.dominio.servicios import ServicioCanonico
from src.normalizadores.normalizador_servicios import NormalizadorServicios


def test_normaliza_texto_conocido_usando_catalogo():
    normalizador = NormalizadorServicios()

    # Debe mapear según las reglas del CatalogoServicios
    resultado = normalizador.normalizar("Limpieza profunda de virus y malware")

    assert resultado == ServicioCanonico.MALWARE


def test_retorna_otro_cuando_no_coincide_con_catalogo():
    normalizador = NormalizadorServicios()

    resultado = normalizador.normalizar("Texto completamente irrelevante 12345")

    assert resultado == ServicioCanonico.OTRO