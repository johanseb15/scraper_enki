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

    if nombre_normalizado == servicio_normalizado or servicio_normalizado in nombre_normalizado:
        return True

    es_buscado_malware = "malware" in servicio_normalizado or "virus" in servicio_normalizado
    es_nombre_malware = "malware" in nombre_normalizado or "virus" in nombre_normalizado

    if es_buscado_malware and es_nombre_malware:
        return True

    return False
