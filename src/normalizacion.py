import unicodedata


def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()

    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )


def es_mismo_servicio(nombre: str, servicio_buscado: str) -> bool:
    nombre_normalizado = normalizar_texto(nombre)
    servicio_normalizado = normalizar_texto(servicio_buscado)

    # 1. Coincidencia exacta o si es parte de la cadena (ej: "mantenimiento" in "mantenimiento de pc")
    if nombre_normalizado == servicio_normalizado or servicio_normalizado in nombre_normalizado:
        return True

    # 2. Flexibilidad para los alias de malware y virus
    # Si ambas cadenas contienen referencias a malware o virus, las tomamos como el mismo servicio
    es_buscado_malware = "malware" in servicio_normalizado or "virus" in servicio_normalizado
    es_nombre_malware = "malware" in nombre_normalizado or "virus" in nombre_normalizado

    if es_buscado_malware and es_nombre_malware:
        return True

    return False
