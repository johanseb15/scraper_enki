import ssl
import time
import urllib.error
import urllib.request

import certifi

from src.dominio.evidencia import DocumentoRaw


class TedFullNoticeClient:
    def __init__(
        self,
        timeout_seconds: float = 30.0,
        retries: int = 1,
        verify_tls: bool = True,
    ):
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self._ssl_context = (
            ssl.create_default_context(cafile=certifi.where())
            if verify_tls
            else ssl._create_unverified_context()
        )

    def obtener(self, documento: DocumentoRaw) -> tuple[int, str, str, dict[str, str]]:
        url = documento.source_url or self._url_directa(documento.source_record_id)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/xml,text/xml,application/json,*/*",
                "User-Agent": "Enki data acquisition",
            },
        )
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout_seconds,
                    context=self._ssl_context,
                ) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    headers = {key: value for key, value in response.headers.items()}
                    return (
                        int(response.status),
                        response.headers.get("Content-Type", "UNKNOWN"),
                        body,
                        headers,
                    )
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                return (
                    int(exc.code),
                    exc.headers.get("Content-Type", "UNKNOWN"),
                    body,
                    {key: value for key, value in exc.headers.items()},
                )
            except (TimeoutError, urllib.error.URLError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    break
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"TED full notice request failed: {last_error}")

    @staticmethod
    def _url_directa(publication_number: str) -> str:
        return f"https://ted.europa.eu/en/notice/{publication_number}/xml"
