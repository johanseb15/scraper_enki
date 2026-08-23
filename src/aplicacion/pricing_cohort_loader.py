from __future__ import annotations

import csv
import os
from decimal import Decimal
from pathlib import Path

from src.aplicacion.pricing_evidence_engine import CohortePricing


DEFAULT_LOCAL_STATS = Path("data/local_pricing_stats_v2.csv")
DEFAULT_REMOTE_STATS = Path("data/remote_pricing_stats_v2.csv")


def _decimal(value: str) -> Decimal:
    return Decimal(str(value))


def cargar_cohortes_pricing(path: str | Path) -> list[CohortePricing]:
    cohortes: list[CohortePricing] = []

    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            cohortes.append(
                CohortePricing(
                    market=row["market"],
                    canonical_service=row["canonical_service"],
                    observations_n=int(row["observations_n"]),
                    providers_n=int(row["providers_n"]),
                    min_ars=_decimal(row["min_ars"]),
                    q1_ars=_decimal(row["q1_ars"]),
                    median_ars=_decimal(row["median_ars"]),
                    q3_ars=_decimal(row["q3_ars"]),
                    max_ars=_decimal(row["max_ars"]),
                    spread_ratio=_decimal(row["spread_ratio"]),
                    evidence_confidence=row["evidence_confidence"],
                    decision_ready=row["decision_ready"].upper() == "YES",
                    range_ready=row["range_ready"].upper() == "YES",
                    price_scope=(row.get("price_scope") or "UNKNOWN"),
                    commercial_context=(row.get("commercial_context") or "STANDARD"),
                )
            )

    return cohortes


def resolver_rutas_pricing_stats() -> tuple[Path, Path]:
    local_path = Path(os.getenv("ENKI_LOCAL_PRICING_STATS", str(DEFAULT_LOCAL_STATS)))
    remote_path = Path(os.getenv("ENKI_REMOTE_PRICING_STATS", str(DEFAULT_REMOTE_STATS)))
    return local_path, remote_path


def cargar_cohortes_pricing_runtime() -> tuple[list[CohortePricing], list[CohortePricing]]:
    local_path, remote_path = resolver_rutas_pricing_stats()
    return cargar_cohortes_pricing(local_path), cargar_cohortes_pricing(remote_path)
