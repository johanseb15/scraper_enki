from datetime import datetime

from bs4 import BeautifulSoup

from src.dominio.evidencia import (
    RegistroPrecioComercialObservado,
)


SOURCE = "bitz_os_installation"
EXTRACTOR_VERSION = "bitz_os_installation_v1"


def _parse_price_ars(
    price_raw: str,
) -> int | None:
    normalized = price_raw.strip()

    if normalized.casefold() in {
        "consultar",
        "consulte",
    }:
        return None

    if not normalized.startswith("$"):
        return None

    numeric = (
        normalized
        .replace("$", "")
        .strip()
        .replace(".", "")
        .replace(",", "")
    )

    if not numeric.isdigit():
        return None

    return int(numeric)


def extraer_observaciones_bitz_os(
    html: str,
    *,
    source_url: str,
    raw_document_id: int,
    retrieved_at: datetime,
    content_hash: str | None = None,
) -> list[
    RegistroPrecioComercialObservado
]:
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    target_details = None

    for details in soup.find_all("details"):
        summary = details.find("summary")

        if summary is None:
            continue

        summary_text = summary.get_text(
            " ",
            strip=True,
        )

        if (
            summary_text
            == "Formateo + Configuración"
        ):
            target_details = details
            break

    if target_details is None:
        return []

    observaciones: list[
        RegistroPrecioComercialObservado
    ] = []

    for item in target_details.select(
        "li.equipo-line"
    ):
        price_span = item.select_one(
            "span.precio-equipo"
        )

        if price_span is None:
            continue

        price_raw = price_span.get_text(
            " ",
            strip=True,
        )

        price_value = _parse_price_ars(
            price_raw
        )

        if price_value is None:
            continue

        full_text = item.get_text(
            " ",
            strip=True,
        )

        price_text = price_span.get_text(
            " ",
            strip=True,
        )

        device_type_raw = (
            full_text
            .removesuffix(price_text)
            .strip()
        )

        source_record_id = (
            "formateo-configuracion:"
            + device_type_raw
            .casefold()
            .replace(" ", "-")
        )

        metadata = {
            "retrieved_at": (
                retrieved_at.isoformat()
            ),
            "currency_evidence": (
                "website_state_currency_title"
            ),
        }

        if content_hash is not None:
            metadata["content_hash"] = (
                content_hash
            )

        observaciones.append(
            RegistroPrecioComercialObservado(
                raw_document_id=(
                    raw_document_id
                ),
                source=SOURCE,
                source_record_id=(
                    source_record_id
                ),
                source_url=source_url,
                extractor_version=(
                    EXTRACTOR_VERSION
                ),
                extraction_status=(
                    "EXTRACTED"
                ),
                provider_raw="Bitz",
                economic_object_raw=(
                    "Formateo + Configuración"
                ),
                scope_raw={
                    "device_type": (
                        device_type_raw
                    ),
                },
                price_raw=price_raw,
                price_value=price_value,
                currency_raw="ARS",
                device_type_raw=(
                    device_type_raw
                ),
                operating_system_raw=(
                    "UNKNOWN"
                ),
                backup_raw="UNKNOWN",
                drivers_raw="UNKNOWN",
                programs_raw="UNKNOWN",
                license_raw="UNKNOWN",
                modality_raw="UNKNOWN",
                comparable_status=(
                    "INDETERMINATE"
                ),
                metadata=metadata,
                rejection_reason="",
            )
        )

    return observaciones