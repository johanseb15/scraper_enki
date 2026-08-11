import json
import ssl
import urllib.parse
import urllib.request
from typing import Any

from src.aplicacion.colector_argentina_bulk import RecursoArgentinaBulk


class DatosArgentinaClient:
    api_base = "https://datos.gob.ar/api/3/action"

    def __init__(self, timeout_seconds: float = 120.0, verify_tls: bool = True):
        self.timeout_seconds = timeout_seconds
        self._ssl_context = ssl.create_default_context() if verify_tls else ssl._create_unverified_context()

    def recursos_dataset(self, dataset_id: str = "sistema-de-contrataciones-electronicas") -> list[RecursoArgentinaBulk]:
        data = self._json("package_show", {"id": dataset_id})
        resources = []
        for raw in data["result"].get("resources", []):
            if str(raw.get("format") or "").upper() != "CSV":
                continue
            resource_type = self._resource_type(raw.get("name", ""))
            resources.append(
                RecursoArgentinaBulk(
                    resource_id=raw["id"],
                    name=raw.get("name") or raw["id"],
                    url=raw["url"],
                    resource_type=resource_type,
                    value_class=self._value_class(resource_type, raw.get("name", "")),
                    metadata={
                        "created": raw.get("created"),
                        "last_modified": raw.get("last_modified"),
                        "metadata_modified": raw.get("metadata_modified"),
                        "description": raw.get("description"),
                        "format": raw.get("format"),
                        "mimetype": raw.get("mimetype"),
                    },
                )
            )
        return resources

    def descargar(self, recurso: RecursoArgentinaBulk) -> tuple[bytes, dict[str, str]]:
        request = urllib.request.Request(recurso.url, headers={"User-Agent": "Codex Enki data acquisition"})
        with urllib.request.urlopen(request, timeout=self.timeout_seconds, context=self._ssl_context) as response:
            body = response.read()
            headers = {key.lower(): value for key, value in response.headers.items()}
            headers["status"] = str(response.status)
            return body, headers

    def _json(self, action: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.api_base}/{action}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": "Codex Enki data acquisition", "Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout_seconds, context=self._ssl_context) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _resource_type(name: str) -> str:
        lowered = name.lower()
        if "adjudic" in lowered:
            return "adjudicaciones"
        if "convocatoria" in lowered:
            return "convocatorias"
        if "sipro" in lowered or "proveedor" in lowered:
            return "sipro"
        if "sibys" in lowered or "cat?logo" in lowered or "catalogo" in lowered:
            return "sibys"
        return "other"

    @staticmethod
    def _value_class(resource_type: str, name: str) -> str:
        lowered = name.lower()
        if resource_type == "adjudicaciones" and "2016 - 2026" in lowered:
            return "P0_ECONOMIC"
        if resource_type == "convocatorias" and "2016 - 2026" in lowered:
            return "P1_MARKET_ACTIVITY"
        if resource_type == "sipro" and "2016-2026" in lowered:
            return "P1_SUPPLIER_INTELLIGENCE"
        if resource_type == "sibys":
            return "P1_TAXONOMY"
        return "P2_HISTORICAL"
