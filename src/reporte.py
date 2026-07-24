import unicodedata

from src.estadisticas import (
    calcular_precio_promedio,
    calcular_precio_minimo,
    calcular_precio_maximo,
)


def _normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()

    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )


def _es_mismo_servicio(
    nombre: str,
    servicio_buscado: str,
) -> bool:
    nombre_normalizado = _normalizar_texto(nombre)
    servicio_normalizado = _normalizar_texto(servicio_buscado)

    return (
        nombre_normalizado == servicio_normalizado
        or (
            servicio_normalizado in nombre_normalizado
            and "malware" in nombre_normalizado
        )
    )


def generar_resumen_servicio(
    datos,
    servicio: str,
):
    filtrados = [
        d for d in datos
        if _es_mismo_servicio(d.servicio, servicio)
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
    }