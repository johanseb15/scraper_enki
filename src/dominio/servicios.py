from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ServicioInfo:
    id: "ServicioCanonico"
    nombre: str


class ServicioCanonico(Enum):
    MALWARE = "malware"
    FORMATEO = "formateo"
    MANTENIMIENTO = "mantenimiento"
    SOPORTE_REDES = "soporte_redes"
    OTRO = "otro"
    DESCONOCIDO = "DESCONOCIDO"


CATALOGO_SERVICIOS = {
    ServicioCanonico.MALWARE: ServicioInfo(
        id=ServicioCanonico.MALWARE, nombre="Eliminación de malware"
    ),
    ServicioCanonico.FORMATEO: ServicioInfo(
        id=ServicioCanonico.FORMATEO, nombre="Formateo e instalación de SO"
    ),
    ServicioCanonico.MANTENIMIENTO: ServicioInfo(
        id=ServicioCanonico.MANTENIMIENTO, nombre="Mantenimiento preventivo"
    ),
    ServicioCanonico.SOPORTE_REDES: ServicioInfo(
        id=ServicioCanonico.SOPORTE_REDES, nombre="Diagnóstico y soporte de redes"
    ),
}


def obtener_servicio(servicio: ServicioCanonico) -> ServicioInfo | None:
    return CATALOGO_SERVICIOS.get(servicio)


@dataclass(frozen=True)
class DetalleServicioCanonico:
    categoria: str
    subcategoria: str
    nombre_normalizado: str
    equipo: str | None = None
    modalidad: str | None = None
    confianza: float = 1.0
    regla_aplicada: str | None = None
