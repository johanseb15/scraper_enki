from .normalizador_ofertas import NormalizadorOfertas, ServicioCanonico

def normalizar_texto(texto: str) -> str:
    """Normaliza texto eliminando espacios extra y convirtiendo a minúsculas."""
    if not texto:
        return ""
    return " ".join(texto.lower().split())

def es_mismo_servicio(s1: str, s2: str) -> bool:
    """Compara si dos nombres o cadenas representan el mismo servicio."""
    return normalizar_texto(s1) == normalizar_texto(s2)

__all__ = [
    "NormalizadorOfertas",
    "ServicioCanonico",
    "normalizar_texto",
    "es_mismo_servicio",
]