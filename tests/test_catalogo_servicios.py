import pytest
from src.dominio.servicios import (
    CATALOGO_SERVICIOS,
    ServicioCanonico,
    obtener_servicio,
)

@pytest.mark.parametrize(
    "enum_servicio, nombre_esperado",
    [
        (ServicioCanonico.MALWARE, "Eliminación de malware"),
        (ServicioCanonico.FORMATEO, "Formateo e instalación de SO"),
        (ServicioCanonico.MANTENIMIENTO, "Mantenimiento preventivo"),
        (ServicioCanonico.SOPORTE_REDES, "Diagnóstico y soporte de redes"),
    ],
)
def test_catalogo_contiene_servicios_canonicos(enum_servicio, nombre_esperado):
    servicio = CATALOGO_SERVICIOS[enum_servicio]

    assert servicio.id == enum_servicio
    assert servicio.nombre == nombre_esperado

def test_obtener_servicio_existente():
    servicio = obtener_servicio(ServicioCanonico.MALWARE)
    assert servicio is not None
    assert servicio.nombre == "Eliminación de malware"


def test_obtener_servicio_inexistente_retorna_none():
    servicio = obtener_servicio("clave_inexistente")
    assert servicio is None
