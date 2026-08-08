import pytest

from src.dominio.catalogos.servicios import CatalogoServicios
from src.dominio.servicios import ServicioCanonico


def test_catalogo_resuelve_servicio_por_sinonimo():
    catalogo = CatalogoServicios()

    servicio = catalogo.resolver_desde_raw("Limpieza de virus")

    assert servicio is not None
    assert servicio.id == ServicioCanonico.MALWARE
    assert servicio.categoria == "Seguridad IT"


def test_catalogo_resuelve_servicio_por_nombre_exacto():
    catalogo = CatalogoServicios()

    servicio = catalogo.resolver_desde_raw("Soporte Técnico Informático")

    assert servicio is not None
    assert servicio.id == ServicioCanonico.SOPORTE_TECNICO


def test_catalogo_retorna_none_si_texto_no_coincide():
    catalogo = CatalogoServicios()

    servicio = catalogo.resolver_desde_raw("Catering para eventos")

    assert servicio is None


def test_catalogo_obtiene_servicio_por_enum_canonico():
    catalogo = CatalogoServicios()

    servicio = catalogo.obtener_por_canonico(ServicioCanonico.MALWARE)

    assert servicio is not None
    assert servicio.nombre_display == "Eliminación de Malware y Virus"


@pytest.mark.parametrize(
    "texto_raw,esperado",
    [
        ("Eliminación de malware", ServicioCanonico.MALWARE),
        ("Eliminación de malware / spyware", ServicioCanonico.MALWARE),
        ("  ELIMINACIÓN DE MALWARE  ", ServicioCanonico.MALWARE),
        ("Limpieza virus PC", ServicioCanonico.MALWARE),
        ("Formateo e instalación de SO", ServicioCanonico.FORMATEO),
        ("Instalación de SO", ServicioCanonico.FORMATEO),
        ("Instalación de Windows 11", ServicioCanonico.FORMATEO),
        ("Mantenimiento preventivo", ServicioCanonico.MANTENIMIENTO),
        ("Limpieza física de PC", ServicioCanonico.MANTENIMIENTO),
        ("Diagnóstico y soporte de redes", ServicioCanonico.SOPORTE_REDES),
        ("Configuración de router", ServicioCanonico.SOPORTE_REDES),
        ("Soporte Técnico Informático", ServicioCanonico.SOPORTE_TECNICO),
    ],
)
def test_catalogo_cubre_aliases_protegidos_por_normalizacion(texto_raw, esperado):
    catalogo = CatalogoServicios()

    servicio = catalogo.resolver_desde_raw(texto_raw)

    assert servicio is not None
    assert servicio.id == esperado
