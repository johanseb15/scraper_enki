from src.estadisticas import (
    calcular_precio_promedio,
    calcular_precio_minimo,
    calcular_precio_maximo,
)
from src.normalizadores.normalizador_servicios import NormalizadorServicios


def generar_resumen_servicio(
    datos,
    servicio: str,
):
    servicio_canonico = NormalizadorServicios().normalizar(servicio)
    filtrados = [
        d for d in datos
        if d.servicio == servicio_canonico
    ]

    if not filtrados:
        return {
            "servicio": servicio,
            "cantidad": 0,
            "precio_minimo": None,
            "precio_promedio": None,
            "precio_maximo": None,
            "empresas_relevadas": 0,
        }

    precios_por_empresa = {}
    for oferta in filtrados:
        precios_por_empresa.setdefault(oferta.empresa.nombre, []).append(
            {
                "modalidad": oferta.modalidad,
                "precio": oferta.precio,
            }
        )

    return {
        "servicio": servicio,
        "cantidad": len(filtrados),
        "precio_minimo": calcular_precio_minimo(filtrados),
        "precio_promedio": calcular_precio_promedio(filtrados),
        "precio_maximo": calcular_precio_maximo(filtrados),
        "empresas_relevadas": len(
            {d.empresa for d in filtrados}
        ),
        "precios_por_empresa": precios_por_empresa,
    }
