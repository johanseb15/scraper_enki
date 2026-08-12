from __future__ import annotations

from datetime import datetime
import re

from bs4 import BeautifulSoup

from src.dominio.evidencia import RegistroPrecioComercialObservado


EXTRACTOR_VERSION = "jadetech_os_installation_v1"
SOURCE = "jadetech_os_installation"
PROVIDER = "Jadetech"


def _texto(nodo) -> str:
    return " ".join(nodo.get_text(" ", strip=True).split()) if nodo else ""


def _precio_a_entero(precio_raw: str) -> int | None:
    limpio = re.sub(r"[^\d,]", "", precio_raw or "")
    if not limpio:
        return None
    entero = limpio.split(",", 1)[0]
    if not entero:
        return None
    return int(entero)


def _source_record_id(service_raw: str, source_url: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", service_raw.lower()).strip("-")
    return f"{source_url}#{slug}"


def extraer_observaciones_jadetech_os(
    html: str,
    *,
    source_url: str,
    raw_document_id: int,
    retrieved_at: datetime,
    content_hash: str | None = None,
) -> list[RegistroPrecioComercialObservado]:
    soup = BeautifulSoup(html or "", "html.parser")
    observaciones: list[RegistroPrecioComercialObservado] = []
    for producto in soup.select(".product"):
        service_raw = _texto(producto.select_one("h2, h1"))
        price_raw = _texto(producto.select_one(".price, .woocommerce-Price-amount"))
        service_lower = service_raw.lower()
        if not service_raw or "sistema operativo" not in service_lower:
            continue
        if "backup" not in service_lower:
            continue
        if not re.search(r"sin\s+backup", service_raw, re.IGNORECASE):
            continue
        if re.search(r"limpieza|hardware|ssd|programas", service_raw, re.IGNORECASE):
            continue
        price_value = _precio_a_entero(price_raw)
        if price_value is None:
            continue
        observaciones.append(
            RegistroPrecioComercialObservado(
                raw_document_id=raw_document_id,
                source=SOURCE,
                source_record_id=_source_record_id(service_raw, source_url),
                source_url=source_url,
                extractor_version=EXTRACTOR_VERSION,
                extraction_status="EXTRACTED",
                provider_raw=PROVIDER,
                economic_object_raw=service_raw,
                scope_raw=service_raw,
                price_raw=price_raw,
                price_value=price_value,
                currency_raw="ARS" if "$" in price_raw else "UNKNOWN",
                device_type_raw="UNKNOWN",
                operating_system_raw="UNKNOWN",
                backup_raw="NO",
                drivers_raw="UNKNOWN",
                programs_raw="UNKNOWN",
                license_raw="UNKNOWN",
                modality_raw="UNKNOWN",
                comparable_status="COMPARABLE_CORE",
                metadata={
                    "retrieved_at": retrieved_at.isoformat(),
                    "content_hash": content_hash or "UNKNOWN",
                    "cohort_contract": {
                        "backup": "NO explícito",
                        "hardware_included": "NO",
                        "data_recovery_included": "NO",
                        "broad_repair_package": "NO",
                    },
                },
            )
        )
    return observaciones
