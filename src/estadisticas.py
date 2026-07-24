from src.modelos.servicio_precio import ServicioPrecio


def _es_mismo_servicio(nombre: str, servicio_buscado: str) -> bool:
    nombre_normalizado = nombre.lower().strip()
    servicio_normalizado = servicio_buscado.lower().strip()

    return (
        nombre_normalizado == servicio_normalizado
        or (
            servicio_normalizado in nombre_normalizado
            and "malware" in nombre_normalizado
        )
    )


def calcular_precio_promedio(
    datos: list[ServicioPrecio],
    servicio: str,
) -> int:
    precios = [
        item.precio_freelance
        for item in datos
        if _es_mismo_servicio(item.servicio, servicio)
    ]

    if not precios:
        raise ValueError(f"{servicio}: sin datos relevados")

    return sum(precios) // len(precios)


def calcular_precio_minimo(
    datos: list[ServicioPrecio],
    servicio: str,
) -> int:
    precios = [
        item.precio_freelance
        for item in datos
        if _es_mismo_servicio(item.servicio, servicio)
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
        if _es_mismo_servicio(item.servicio, servicio)
    ]

    if not precios:
        raise ValueError(f"{servicio}: sin datos relevados")

    return max(precios)