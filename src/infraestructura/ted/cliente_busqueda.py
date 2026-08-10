import json
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

import certifi


class TedPublicSearchClient:
    endpoint = "https://api.ted.europa.eu/v3/notices/search"

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        retries: int = 2,
        page_size: int = 250,
        verify_tls: bool = True,
    ):
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.page_size = min(page_size, 250)
        self._ssl_context = (
            ssl.create_default_context(cafile=certifi.where())
            if verify_tls
            else ssl._create_unverified_context()
        )

    def buscar(self, *, query: str, limit: int) -> list[dict[str, Any]]:
        registros: list[dict[str, Any]] = []
        page = 1
        while len(registros) < limit:
            batch_limit = min(self.page_size, limit - len(registros))
            payload = self._payload(query=query, page=page, limit=batch_limit)
            response = self._post_json(payload)
            notices = response.get("notices")
            if not isinstance(notices, list):
                raise ValueError("TED response missing notices list")
            registros.extend(notice for notice in notices if isinstance(notice, dict))
            if len(notices) < batch_limit:
                break
            page += 1
        return registros[:limit]

    def _payload(self, *, query: str, page: int, limit: int) -> dict[str, Any]:
        return {
            "query": query,
            "fields": [
                "publication-number",
                "notice-title",
                "publication-date",
                "buyer-name",
                "buyer-country",
                "classification-cpv",
                "procedure-type",
                "notice-type",
                "description-lot",
            ],
            "page": page,
            "limit": limit,
            "scope": "ALL",
            "checkQuerySyntax": False,
            "paginationMode": "PAGE_NUMBER",
            "onlyLatestVersions": True,
        }

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout_seconds,
                    context=self._ssl_context,
                ) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    break
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"TED request failed: {last_error}")
