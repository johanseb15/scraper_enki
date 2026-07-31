from src.estadisticas import (
    calcular_precio_promedio,
    calcular_precio_minimo,
    calcular_precio_maximo,
)
from src.normalizacion import es_mismo_servicio


def generar_resumen_servicio(
    datos,
    servicio: str,
):
    filtrados = [
        d for d in datos
        if es_mismo_servicio(d.servicio, servicio)
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

    return {
        "servicio": servicio,
        "cantidad": len(filtrados),
        "precio_minimo": calcular_precio_minimo(datos, servicio),
        "precio_promedio": calcular_precio_promedio(datos, servicio),
        "precio_maximo": calcular_precio_maximo(datos, servicio),
        "empresas_relevadas": len(
            {d.empresa for d in filtrados}
        ),
        "precios_por_empresa": {
            d.empresa: d.precio_freelance
            for d in filtrados
        },
    }
