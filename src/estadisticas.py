from src.modelos.servicio_precio import ServicioPrecio


def calcular_precio_promedio(
    datos: list[ServicioPrecio],
    servicio: str,
) -> int:
    precios = [
        item.precio_freelance
        for item in datos
        if item.servicio == servicio
    ]

    return sum(precios) // len(precios)

def calcular_precio_minimo(
    datos: list[ServicioPrecio],
    servicio: str,
) -> int:
    precios = [
        item.precio_freelance
        for item in datos
        if item.servicio == servicio
    ]
    if not precios:
        raise ValueError(f"{servicio}: sin datos relevados")
    
    return min(precios)

def calcular_precio_maximo(
        datos: list[ServicioPrecio],
        servicio: str,
) -> int:
    precios = [
        item.precio_freelance
        for item in datos
        if item.servicio == servicio
    ]

    if not precios:
        raise ValueError(f"{servicio}: sin datos relevados")

    return max(precios)

def calcular_precio_promedio(datos: list[ServicioPrecio], servicio: str) -> int:
    precios = [
        item.precio_freelance
        for item in datos
        if item.servicio == servicio
    ]

    if not precios:
        raise ValueError(f"{servicio}: sin datos relevados")    
    
    return sum(precios) // len(precios)