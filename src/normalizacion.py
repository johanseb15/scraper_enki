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

    return (
        nombre_normalizado == servicio_normalizado
        or (
            servicio_normalizado in nombre_normalizado
            and "malware" in nombre_normalizado
        )
    )