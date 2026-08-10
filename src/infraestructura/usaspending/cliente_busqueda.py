import json
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

import certifi

from src.aplicacion.colector_usaspending import USASPENDING_QUERY


class USASpendingClient:
    endpoint = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

    fields = [
        "Award ID",
        "Recipient Name",
        "Recipient UEI",
        "Award Amount",
        "Potential Award Amount",
        "Start Date",
        "End Date",
        "Awarding Agency",
        "Awarding Sub Agency",
        "Awarding Office",
        "Funding Agency",
        "Funding Sub Agency",
        "Contract Award Type",
        "Contract Description",
        "Description",
        "NAICS",
        "PSC",
        "Place of Performance State Code",
        "Place of Performance Country Code",
        "generated_internal_id",
    ]

    def __init__(
        self,
        timeout_seconds: float = 60.0,
        retries: int = 2,
        page_size: int = 100,
        verify_tls: bool = True,
    ):
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.page_size = page_size
        self._ssl_context = (
            ssl.create_default_context(cafile=certifi.where())
            if verify_tls
            else ssl._create_unverified_context()
        )

    def buscar_awards(self, *, limit: int) -> list[dict[str, Any]]:
        awards: list[dict[str, Any]] = []
        page = 1
        while len(awards) < limit:
            batch_limit = min(self.page_size, limit - len(awards))
            payload = self._payload(page=page, limit=batch_limit)
            data = self._post_json(payload)
            results = data.get("results")
            if not isinstance(results, list):
                raise ValueError("USASpending response missing results list")
            awards.extend(item for item in results if isinstance(item, dict))
            page_metadata = data.get("page_metadata") or {}
            if not page_metadata.get("hasNext") or len(results) < batch_limit:
                break
            page += 1
        return awards[:limit]

    def _payload(self, *, page: int, limit: int) -> dict[str, Any]:
        return {
            "filters": USASPENDING_QUERY,
            "fields": self.fields,
            "sort": "Award Amount",
            "order": "desc",
            "page": page,
            "limit": limit,
            "subawards": False,
        }

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
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
        raise RuntimeError(f"USASpending request failed: {last_error}")
