from src.dominio.servicios import (
    ServicioCanonico,
    DetalleServicioCanonico,
    CATALOGO_SERVICIOS,
)
from src.normalizacion import normalizar_texto

MAPEO_SERVICIOS = {
    "malware": ServicioCanonico.MALWARE,
    "virus": ServicioCanonico.MALWARE,
    "spyware": ServicioCanonico.MALWARE,
    "troyanos": ServicioCanonico.MALWARE,

    "formateo": ServicioCanonico.FORMATEO,
    "instalacion de so": ServicioCanonico.FORMATEO,
    "windows 11": ServicioCanonico.FORMATEO,
    "reinstalacion": ServicioCanonico.FORMATEO,

    "mantenimiento": ServicioCanonico.MANTENIMIENTO,
    "limpieza fisica": ServicioCanonico.MANTENIMIENTO,

    "redes": ServicioCanonico.SOPORTE_REDES,
    "router": ServicioCanonico.SOPORTE_REDES,
    "soporte de redes": ServicioCanonico.SOPORTE_REDES,
}


class NormalizadorServicios:

    def normalizar(self, texto: str) -> ServicioCanonico:
        texto_limpio = normalizar_texto(texto).lower()

        for clave, servicio in MAPEO_SERVICIOS.items():
            if clave in texto_limpio:
                return servicio

        return ServicioCanonico.DESCONOCIDO

    def normalizar_avanzado(self, texto: str) -> DetalleServicioCanonico:
        texto_limpio = normalizar_texto(texto).lower()

        for clave, servicio in MAPEO_SERVICIOS.items():
            if clave in texto_limpio:
                info = CATALOGO_SERVICIOS.get(servicio)

                return DetalleServicioCanonico(
                    categoria="soporte_tecnico",
                    subcategoria=servicio.value,
                    nombre_normalizado=info.nombre if info else servicio.value,
                    confianza=0.95,
                    regla_aplicada=f"alias_{clave}",
                )

        return DetalleServicioCanonico(
            categoria="desconocido",
            subcategoria="desconocido",
            nombre_normalizado=texto,
            confianza=0.0,
            regla_aplicada="fallback_original",
        )
