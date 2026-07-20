from src.estadisticas import (
    calcular_precio_promedio,
    calcular_precio_minimo,
    calcular_precio_maximo,
)


def generar_resumen_servicio(
    datos,
    servicio: str,
):
    filtrados = [
        d for d in datos
        if d.servicio == servicio
    ]

    return {
        "servicio": servicio,
        "cantidad": len(filtrados),
        "precio_minimo": calcular_precio_minimo(datos, servicio),
        "precio_promedio": calcular_precio_promedio(datos, servicio),
        "precio_maximo": calcular_precio_maximo(datos, servicio),
    }