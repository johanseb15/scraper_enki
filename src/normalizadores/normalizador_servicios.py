from dataclasses import dataclass
from enum import Enum, auto
import re
import unicodedata

class ServicioCanonico(Enum):
    FORMATEO = auto()
    MANTENIMIENTO = auto()
    SOPORTE_REDES = auto()
    INSTALACION_SO = auto()
    DIAGNOSTICO = auto()
    DESCONOCIDO = auto()
    OTRO = auto()


@dataclass
class DetalleServicioCanonico:
    servicio: ServicioCanonico
    categoria: str
    subcategoria: str | None = None
    confianza: float = 1.0


class NormalizadorServicios:
    # Mapeo de frases clave a ServicioCanonico
    MAPEO_KEYWORDS = {
        ServicioCanonico.FORMATEO: [
            "formateo", "formatear", "instalacion de windows", "reinstalacion de sistema", "reinstalacion so"
        ],
        ServicioCanonico.MANTENIMIENTO: [
            "mantenimiento", "limpieza fisica", "mantenimiento preventivo", "cambio de pasta termica"
        ],
        ServicioCanonico.SOPORTE_REDES: [
            "redes", "router", "configuracion de router", "soporte de red", "instalacion de red", "wifi"
        ],
        ServicioCanonico.INSTALACION_SO: [
            "instalacion sistema operativo", "instalar windows", "instalar linux"
        ],
        ServicioCanonico.DIAGNOSTICO: [
            "diagnostico", "revision", "presupuesto", "chequeo"
        ],
    }

    # Categorías asociadas a cada servicio para el análisis avanzado
    CATEGORIAS = {
        ServicioCanonico.FORMATEO: "Software",
        ServicioCanonico.MANTENIMIENTO: "Hardware",
        ServicioCanonico.SOPORTE_REDES: "Conectividad",
        ServicioCanonico.INSTALACION_SO: "Software",
        ServicioCanonico.DIAGNOSTICO: "General",
        ServicioCanonico.DESCONOCIDO: "Sin Clasificar",
        ServicioCanonico.OTRO: "General",
    }

    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """Limpia acentos, caracteres especiales y convierte a minúsculas."""
        if not texto:
            return ""
        # Normaliza Unicode NFD para separar acentos y diacríticos
        texto_nfd = unicodedata.normalize("NFD", texto)
        texto_sin_acentos = "".join(
            c for c in texto_nfd if unicodedata.category(c) != "Mn"
        )
        return re.sub(r"\s+", " ", texto_sin_acentos.lower()).strip()

    def normalizar(self, descripcion: str) -> ServicioCanonico:
        """Determina el ServicioCanonico según el texto ingresado."""
        texto_limpio = self.normalizar_texto(descripcion)

        if not texto_limpio:
            return ServicioCanonico.DESCONOCIDO

        for servicio, keywords in self.MAPEO_KEYWORDS.items():
            for kw in keywords:
                if kw in texto_limpio:
                    return servicio

        return ServicioCanonico.DESCONOCIDO

    def normalizar_avanzado(self, descripcion: str) -> DetalleServicioCanonico:
        """Retorna un objeto DetalleServicioCanonico con metadatos de categoría."""
        servicio_canonico = self.normalizar(descripcion)
        categoria = self.CATEGORIAS.get(servicio_canonico, "General")

        return DetalleServicioCanonico(
            servicio=servicio_canonico,
            categoria=categoria,
            confianza=1.0 if servicio_canonico != ServicioCanonico.DESCONOCIDO else 0.0,
        )