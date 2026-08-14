from __future__ import annotations

from dataclasses import dataclass
import csv
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Iterable


OUTPUT_FIELDS = (
    "observation_id",
    "source",
    "province",
    "city",
    "economic_object_raw",
    "price_value",
    "currency",
    "semantic_role",
    "market_scope",
    "matched_services",
    "canonical_service",
    "comparability_key",
    "original_comparable_status",
    "extractor_version",
)


@dataclass(frozen=True)
class SemanticClassification:
    semantic_role: str
    market_scope: str
    matched_services: str = ""
    canonical_service: str = ""
    comparability_key: str = ""


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    ).lower()


def _clean_for_semantics(text: str) -> str:
    """Remove presentation badges without modifying preserved raw evidence."""
    x = re.sub(
        r"\bmas\s+popular\b",
        " ",
        _fold(text),
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", x).strip()


def _local_key(province: str, canonical_service: str) -> str:
    if not province or not canonical_service:
        return ""
    return f"{province}::{canonical_service}"


def classify_new_observation(
    economic_object_raw: str,
    *,
    province: str,
) -> SemanticClassification:
    """Conservative extension rules for observations absent from frozen v4.

    This function intentionally emits no comparable canonical cohort when the
    object appears to be hardware or a composite service.
    """
    x = _clean_for_semantics(economic_object_raw)

    # Goods/hardware: strong component/spec language means this is not a service.
    hardware_signals = (
        r"\bryzen\s+\d",
        r"\b(?:rtx|gtx|rx)\s*\d{3,4}\b",
        r"\b(?:ddr\d|ram)\b",
        r"\b(?:ssd|nvme)\s*\d+\s*(?:gb|tb)\b",
        r"\bcpu\b",
        r"\bgpu\b",
    )
    if sum(bool(re.search(p, x)) for p in hardware_signals) >= 2:
        return SemanticClassification(
            semantic_role="HARDWARE_PRODUCT",
            market_scope="GOODS_MARKET",
        )

    # OS installation maps to the canonical used by semantic_normalization_v4.
    if re.search(
        r"\b(?:instalacion|instalar)\b.*\b(?:sistema operativo|windows|so)\b",
        x,
    ):
        canonical = "FORMATEO_INSTALACION_SO"
        return SemanticClassification(
            semantic_role="SINGLE_SERVICE",
            market_scope="LOCAL_SERVICE",
            matched_services=canonical,
            canonical_service=canonical,
            comparability_key=_local_key(province, canonical),
        )

    # Existing v4 canonical: REPARACION_INICIO_WINDOWS.
    if (
        re.search(r"\b(?:pc|notebook|equipo)\b", x)
        and re.search(r"\bno\s+inicia\b|\bno\s+arranca\b", x)
        and not re.search(r"\bno\s+enciende\b", x)
    ):
        canonical = "REPARACION_INICIO_WINDOWS"
        return SemanticClassification(
            semantic_role="SINGLE_SERVICE",
            market_scope="LOCAL_SERVICE",
            matched_services=canonical,
            canonical_service=canonical,
            comparability_key=_local_key(province, canonical),
        )

    # Disk replacement + cloning is explicitly composite. Do not fabricate
    # allocation between labor, hardware handling and data migration.
    if (
        re.search(r"\b(?:cambio|cambiar|reemplazo)\b.*\bdisco\b", x)
        and re.search(r"\bclon(?:ado|acion|ar)\b", x)
    ):
        return SemanticClassification(
            semantic_role="COMPOSITE_SERVICE",
            market_scope="MIXED_OR_UNKNOWN",
            matched_services="REPARACION_HW|BACKUP_DATOS",
        )

    # Conservative fallback: preserve observation but keep it out of pricing
    # cohorts until a deliberate semantic rule exists.
    return SemanticClassification(
        semantic_role="UNMAPPED",
        market_scope="UNKNOWN",
    )


def _json_scalar(raw: str):
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return raw


def _baseline_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        (row.get("source") or "").strip(),
        (row.get("economic_object_raw") or "").strip(),
        str(row.get("price_value") or "").strip(),
        (row.get("currency") or "").strip(),
    )


def load_frozen_baseline(path: str | Path) -> dict[tuple[str, str, str, str], dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {_baseline_key(row): row for row in rows}


def _normalize_number_for_key(value) -> str:
    if value is None:
        return ""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if num.is_integer():
        return str(int(num))
    return str(num)


def _live_key(
    source: str,
    economic_object: str,
    price_value,
    currency: str,
) -> tuple[str, str, str, str]:
    return (
        source.strip(),
        economic_object.strip(),
        _normalize_number_for_key(price_value),
        currency.strip(),
    )


def build_semantic_rows(
    db_path: str | Path,
    *,
    baseline_path: str | Path,
) -> tuple[list[dict[str, str]], int, int]:
    baseline = load_frozen_baseline(baseline_path)

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                o.id AS observation_id,
                o.source,
                o.economic_object_raw_json,
                o.price_value_json,
                o.currency_raw_json,
                o.comparable_status,
                o.extractor_version,
                r.metadata_json
            FROM commercial_price_observations o
            JOIN raw_documents r
              ON r.id = o.raw_document_id
            ORDER BY o.id
            """
        ).fetchall()

    output: list[dict[str, str]] = []
    reused = 0
    newly_classified = 0

    for row in rows:
        economic_object = _json_scalar(row["economic_object_raw_json"])
        price_value = _json_scalar(row["price_value_json"])
        currency = _json_scalar(row["currency_raw_json"])
        metadata = _json_scalar(row["metadata_json"]) or {}

        economic_object = str(economic_object or "")
        currency = str(currency or "")
        province = str(metadata.get("province") or "")
        city = str(metadata.get("city") or "")

        key = _live_key(
            row["source"],
            economic_object,
            price_value,
            currency,
        )

        frozen = baseline.get(key)
        if frozen is not None:
            reused += 1
            out = dict(frozen)
            # The live observation id is authoritative for this live export.
            out["observation_id"] = str(row["observation_id"])
            output.append({field: out.get(field, "") for field in OUTPUT_FIELDS})
            continue

        newly_classified += 1
        classification = classify_new_observation(
            economic_object,
            province=province,
        )

        output.append({
            "observation_id": str(row["observation_id"]),
            "source": row["source"],
            "province": province,
            "city": city,
            "economic_object_raw": economic_object,
            "price_value": _normalize_number_for_key(price_value),
            "currency": currency,
            "semantic_role": classification.semantic_role,
            "market_scope": classification.market_scope,
            "matched_services": classification.matched_services,
            "canonical_service": classification.canonical_service,
            "comparability_key": classification.comparability_key,
            "original_comparable_status": row["comparable_status"],
            "extractor_version": row["extractor_version"],
        })

    return output, reused, newly_classified


def write_semantic_csv(
    path: str | Path,
    rows: Iterable[dict[str, str]],
) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
