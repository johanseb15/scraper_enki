from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.aplicacion.colector_precios_batch import (
    FuentePricing,
)


DISCOVERY_STATUSES = {
    "DISCOVERED",
    "VERIFIED",
    "REJECTED",
    "DUPLICATE",
}

PRICE_VISIBILITIES = {
    "PRICE_VISIBLE",
    "NO_PRICE_VISIBLE",
    "UNKNOWN",
}

SOURCE_KINDS = {
    "PROVIDER",
    "AGGREGATOR",
    "REFERENCE",
}

REQUIRED_FIELDS = (
    "source",
    "provider",
    "url",
    "province",
    "city",
    "discovery_status",
    "price_visibility",
    "source_kind",
)

OPTIONAL_FIELDS = (
    "notes",
)


@dataclass(frozen=True)
class FuenteDescubierta:
    source: str
    provider: str
    url: str
    province: str
    city: str
    discovery_status: str
    price_visibility: str
    source_kind: str
    notes: str = ""

    @property
    def acquisition_eligible(self) -> bool:
        return (
            self.discovery_status == "VERIFIED"
            and self.price_visibility == "PRICE_VISIBLE"
            and self.source_kind == "PROVIDER"
        )

    def to_fuente_pricing(self) -> FuentePricing:
        return FuentePricing(
            source=self.source,
            provider=self.provider,
            url=self.url,
            province=self.province,
            city=self.city,
        )


def _validar_campos_obligatorios(
    row: dict[str, str],
    *,
    row_number: int,
) -> None:
    for field in REQUIRED_FIELDS:
        value = (row.get(field) or "").strip()

        if not value:
            raise ValueError(
                f"Campo obligatorio faltante "
                f"{field!r} en fila {row_number}"
            )


def _validar_valor(
    value: str,
    *,
    field: str,
    allowed: set[str],
    row_number: int,
) -> str:
    normalized = value.strip().upper()

    if normalized not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(
            f"Valor inválido para {field!r} "
            f"en fila {row_number}: {value!r}. "
            f"Permitidos: {allowed_text}"
        )

    return normalized


def cargar_registry_pricing_csv(
    path: str | Path,
) -> list[FuenteDescubierta]:
    csv_path = Path(path)

    fuentes: list[FuenteDescubierta] = []
    sources_seen: set[str] = set()

    with csv_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as archivo:
        reader = csv.DictReader(archivo)

        if reader.fieldnames is None:
            raise ValueError(
                "El CSV no contiene encabezados"
            )

        missing_headers = [
            field
            for field in REQUIRED_FIELDS
            if field not in reader.fieldnames
        ]

        if missing_headers:
            raise ValueError(
                "Faltan columnas obligatorias: "
                + ", ".join(missing_headers)
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            if not any(
                (value or "").strip()
                for value in row.values()
            ):
                continue

            _validar_campos_obligatorios(
                row,
                row_number=row_number,
            )

            source = row["source"].strip()

            if source in sources_seen:
                raise ValueError(
                    f"source duplicado: {source}"
                )

            sources_seen.add(source)

            discovery_status = _validar_valor(
                row["discovery_status"],
                field="discovery_status",
                allowed=DISCOVERY_STATUSES,
                row_number=row_number,
            )

            price_visibility = _validar_valor(
                row["price_visibility"],
                field="price_visibility",
                allowed=PRICE_VISIBILITIES,
                row_number=row_number,
            )

            source_kind = _validar_valor(
                row["source_kind"],
                field="source_kind",
                allowed=SOURCE_KINDS,
                row_number=row_number,
            )

            fuentes.append(
                FuenteDescubierta(
                    source=source,
                    provider=row["provider"].strip(),
                    url=row["url"].strip(),
                    province=row["province"].strip(),
                    city=row["city"].strip(),
                    discovery_status=discovery_status,
                    price_visibility=price_visibility,
                    source_kind=source_kind,
                    notes=(row.get("notes") or "").strip(),
                )
            )

    return fuentes


def seleccionar_fuentes_pricing(
    fuentes: list[FuenteDescubierta],
) -> list[FuentePricing]:
    return [
        fuente.to_fuente_pricing()
        for fuente in fuentes
        if fuente.acquisition_eligible
    ]


def cargar_fuentes_pricing_csv(
    path: str | Path,
) -> list[FuentePricing]:
    return seleccionar_fuentes_pricing(
        cargar_registry_pricing_csv(path)
    )
