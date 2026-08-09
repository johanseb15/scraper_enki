import requests


def descargar_html(url: str, timeout: int = 15) -> str:
    """Descarga el contenido HTML de una URL enviando un User-Agent estándar."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    encoding = (response.encoding or "").casefold()
    if response.apparent_encoding and encoding in {"", "iso-8859-1", "latin-1"}:
        response.encoding = response.apparent_encoding
    return response.text

