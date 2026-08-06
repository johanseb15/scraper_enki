import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    """Normaliza un texto eliminando acentos, caracteres especiales y convirtiendo a minúsculas."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^\w\s]", "", texto)
    return texto.strip().lower()