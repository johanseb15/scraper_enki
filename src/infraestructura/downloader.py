from __future__ import annotations

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def descargar_html(
    url: str,
    timeout: int = 15,
    *,
    session: requests.Session | None = None,
) -> str:
    """Descarga HTML con verificación TLS activa.

    La sesión inyectable permite que entrypoints de adquisición elijan una
    estrategia TLS segura sin desactivar verificación de certificados.
    """
    client = session or requests
    response = client.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    encoding = (response.encoding or "").casefold()
    if response.apparent_encoding and encoding in {"", "iso-8859-1", "latin-1"}:
        response.encoding = response.apparent_encoding
    return response.text
