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