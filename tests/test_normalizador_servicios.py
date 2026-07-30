import pytest
from src.dominio.servicios import ServicioCanonico
from src.dominio.normalizador_servicios import NormalizadorServicios


@pytest.fixture
def normalizador():
    return NormalizadorServicios()


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("Eliminación de malware", ServicioCanonico.MALWARE),
        ("Eliminación de malware / spyware", ServicioCanonico.MALWARE),
    ],
)
def test_normaliza_servicio_malware(normalizador, entrada, esperado):
    assert normalizador.normalizar(entrada) == esperado


@pytest.mark.parametrize(
    "entrada",
    [
        "Cambio de disco SSD",
        "Servicio inventado",
    ],
)
def test_devuelve_el_nombre_original_si_no_existe_alias(normalizador, entrada):
    assert normalizador.normalizar(entrada) == entrada


@pytest.mark.parametrize(
    "entrada",
    [
        "ELIMINACIÓN DE MALWARE",
        "eliminación de malware",
        " Eliminación de malware ",
        "  ELIMINACIÓN DE MALWARE  ",
    ],
)
def test_normaliza_ignorando_mayusculas_y_espacios(normalizador, entrada):
    assert normalizador.normalizar(entrada) == ServicioCanonico.MALWARE


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("Formateo e instalación de SO", ServicioCanonico.FORMATEO),
        ("Instalación de Windows 11", ServicioCanonico.FORMATEO),
        ("Mantenimiento preventivo", ServicioCanonico.MANTENIMIENTO),
        ("Limpieza física de PC", ServicioCanonico.MANTENIMIENTO),
        ("Diagnóstico y soporte de redes", ServicioCanonico.SOPORTE_REDES),
        ("Configuración de router", ServicioCanonico.SOPORTE_REDES),
    ],
)
def test_normaliza_nuevos_servicios(normalizador, entrada, esperado):
    assert normalizador.normalizar(entrada) == esperado