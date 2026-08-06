from src.normalizadores.normalizador_texto import normalizar_texto


def es_mismo_servicio(s1: str, s2: str) -> bool:
    return normalizar_texto(s1) == normalizar_texto(s2)


__all__ = ["normalizar_texto", "es_mismo_servicio"]