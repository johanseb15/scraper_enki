from src.normalizadores.normalizador_texto import normalizar_texto


def es_mismo_servicio(s1: str, s2: str) -> bool:
    texto_1 = normalizar_texto(s1)
    texto_2 = normalizar_texto(s2)

    if texto_1 == texto_2:
        return True

    from src.dominio.servicios import ServicioCanonico
    from src.normalizadores.normalizador_servicios import NormalizadorServicios

    normalizador = NormalizadorServicios()
    servicio_1 = normalizador.normalizar(texto_1)
    servicio_2 = normalizador.normalizar(texto_2)

    return (
        servicio_1 != ServicioCanonico.DESCONOCIDO
        and servicio_1 == servicio_2
    )


__all__ = ["normalizar_texto", "es_mismo_servicio"]
