import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import certifi


class MercadoPublicoClient:
    base_url = "https://api.mercadopublico.cl/servicios/v1/publico"

    def __init__(
        self,
        ticket: str | None = None,
        timeout_seconds: float = 60.0,
        retries: int = 5,
        request_interval_seconds: float = 0.0,
        verify_tls: bool = True,
    ):
        self.ticket = ticket or os.environ.get("MERCADO_PUBLICO_TICKET")
        if not self.ticket:
            raise ValueError("MERCADO_PUBLICO_TICKET is required")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.request_interval_seconds = request_interval_seconds
        self._ssl_context = (
            ssl.create_default_context(cafile=certifi.where())
            if verify_tls
            else ssl._create_unverified_context()
        )

    def listar_ordenes(self, *, fecha: str, estado: str, limit: int) -> list[dict[str, Any]]:
        params = {"fecha": fecha, "estado": estado, "ticket": self.ticket}
        data = self._get_json("ordenesdecompra.json", params)
        listado = data.get("Listado")
        if not isinstance(listado, list):
            raise ValueError("Mercado Publico response missing Listado")
        return [item for item in listado if isinstance(item, dict)][:limit]

    def obtener_orden(self, codigo: str) -> dict[str, Any]:
        data = self._get_json("ordenesdecompra.json", {"codigo": codigo, "ticket": self.ticket})
        listado = data.get("Listado")
        if not isinstance(listado, list) or not listado:
            raise LookupError(f"order not available: {codigo}")
        detalle = listado[0]
        if not isinstance(detalle, dict):
            raise ValueError(f"invalid order detail: {codigo}")
        return detalle

    def _get_json(self, resource: str, params: dict[str, str]) -> dict[str, Any]:
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}/{resource}?{query}"
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            if self.request_interval_seconds:
                time.sleep(self.request_interval_seconds)
            try:
                request = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(request, timeout=self.timeout_seconds, context=self._ssl_context) as response:
                    body = response.read().decode("utf-8-sig", errors="replace")
                    return json.loads(body)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if attempt >= self.retries:
                    break
                retry_after = exc.headers.get("Retry-After")
                sleep_seconds = float(retry_after) if retry_after else min(60.0, 5.0 * (attempt + 1))
                time.sleep(sleep_seconds)
            except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    break
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"Mercado Publico request failed: {last_error}")
