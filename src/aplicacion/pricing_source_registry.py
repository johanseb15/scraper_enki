from __future__ import annotations

import csv
from pathlib import Path

from src.aplicacion.colector_precios_batch import (
    FuentePricing,
)


REQUIRED_FIELDS = (
    "source",
    "provider",
    "url",
    "province",
    "city",
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


def cargar_fuentes_pricing_csv(
    path: str | Path,
) -> list[FuentePricing]:
    csv_path = Path(path)

    fuentes: list[FuentePricing] = []
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

            fuentes.append(
                FuentePricing(
                    source=source,
                    provider=row["provider"].strip(),
                    url=row["url"].strip(),
                    province=row["province"].strip(),
                    city=row["city"].strip(),
                )
            )

    return fuentes