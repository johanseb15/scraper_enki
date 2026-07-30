from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ServicioCanonico(Enum):
    MALWARE = "malware"
    FORMATEO = "formateo"
    MANTENIMIENTO = "mantenimiento"
    SOPORTE_REDES = "soporte_redes"


@dataclass
class ServicioDominio:
    id: ServicioCanonico
    nombre: str


CATALOGO_SERVICIOS: dict[ServicioCanonico, ServicioDominio] = {
    ServicioCanonico.MALWARE: ServicioDominio(
        id=ServicioCanonico.MALWARE,
        nombre="Eliminación de malware",
    ),
    ServicioCanonico.FORMATEO: ServicioDominio(
        id=ServicioCanonico.FORMATEO,
        nombre="Formateo e instalación de SO",
    ),
    ServicioCanonico.MANTENIMIENTO: ServicioDominio(
        id=ServicioCanonico.MANTENIMIENTO,
        nombre="Mantenimiento preventivo",
    ),
    ServicioCanonico.SOPORTE_REDES: ServicioDominio(
        id=ServicioCanonico.SOPORTE_REDES,
        nombre="Diagnóstico y soporte de redes",
    ),
}


def obtener_servicio(clave: ServicioCanonico | str) -> Optional[ServicioDominio]:
    """Retorna el ServicioDominio según el Enum o None si no existe."""
    return CATALOGO_SERVICIOS.get(clave)  # type: ignore[arg-type]