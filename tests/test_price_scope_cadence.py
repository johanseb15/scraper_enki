from __future__ import annotations

import csv
from pathlib import Path

from scripts.build_pricing_statistics import build_pricing_statistics

FIELDS = [
    "observation_id", "source", "province", "city", "economic_object_raw",
    "price_value", "currency", "semantic_role", "market_scope",
    "matched_services", "canonical_service", "comparability_key",
    "original_comparable_status", "extractor_version",
]


def _row(observation_id: int, source: str, economic_object_raw: str, price_value: int) -> dict[str, str]:
    return {
        "observation_id": str(observation_id),
        "source": source,
        "province": "Buenos Aires",
        "city": "",
        "economic_object_raw": economic_object_raw,
        "price_value": str(price_value),
        "currency": "ARS",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "matched_services": "SOPORTE_REMOTO",
        "canonical_service": "SOPORTE_REMOTO",
        "comparability_key": "AR::SOPORTE_REMOTO",
        "original_comparable_status": "INDETERMINATE",
        "extractor_version": "generic_price_extractor_v3",
    }


def _write_semantic(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_remote_support_is_split_by_price_scope_and_commercial_context(tmp_path):
    semantic = tmp_path / "semantic.csv"
    local_out = tmp_path / "local.csv"
    remote_out = tmp_path / "remote.csv"

    _write_semantic(
        semantic,
        [
            _row(1, "bitz_generic", "Servicio realizado a distancia.", 35000),
            _row(2, "bairescloud_generic", "Conexión Remota x 1 HS PC-Notebook-AIO", 30000),
            _row(3, "informatica_del_plata_ba", "Servicio técnico/Instalaciones por acceso remoto Hora Inicial o fracción $ 10.000 Hora adicional o fracción", 28000),
            _row(4, "informatica_del_plata_ba", "Servicio técnico/Instalaciones por acceso remoto (Urgencias, fines de semana, feriados) Hora Inicial o fracción $ 20.000 Hora adicional o fracción", 48000),
            _row(5, "tecnico_eliseo_cordoba", "Hora servicio técnico remoto", 40000),
        ],
    )

    _, remote = build_pricing_statistics(
        semantic,
        local_out_path=local_out,
        remote_out_path=remote_out,
    )

    support = [
        row for row in remote
        if row["market"] == "AR" and row["canonical_service"] == "SOPORTE_REMOTO"
    ]
    by_key = {(row["price_scope"], row["commercial_context"]): row for row in support}

    unknown = by_key[("UNKNOWN", "UNKNOWN")]
    assert unknown["observations_n"] == 1
    assert unknown["source_count"] == 1
    assert unknown["providers_n"] == 0
    assert unknown["evidence_confidence"] == "INSUFFICIENT"
    assert unknown["range_ready"] == "NO"
    assert unknown["decision_ready"] == "NO"

    hourly = by_key[("PER_HOUR", "UNKNOWN")]
    assert hourly["observations_n"] == 3
    assert hourly["source_count"] == 3
    assert hourly["providers_n"] == 0
    assert hourly["min_ars"] == 28000
    assert hourly["q1_ars"] == 29000
    assert hourly["median_ars"] == 30000
    assert hourly["q3_ars"] == 35000
    assert hourly["max_ars"] == 40000
    assert hourly["evidence_confidence"] == "INSUFFICIENT"
    assert hourly["range_ready"] == "NO"
    assert hourly["decision_ready"] == "NO"

    urgency = by_key[("PER_HOUR", "URGENCY")]
    assert urgency["observations_n"] == 1
    assert urgency["source_count"] == 1
    assert urgency["providers_n"] == 0
    assert urgency["min_ars"] == 48000
    assert urgency["max_ars"] == 48000
    assert urgency["evidence_confidence"] == "INSUFFICIENT"
    assert urgency["decision_ready"] == "NO"

    assert len(support) == 3


def test_scope_detection_does_not_treat_technical_numbers_as_cadence(tmp_path):
    semantic = tmp_path / "semantic.csv"
    local_out = tmp_path / "local.csv"
    remote_out = tmp_path / "remote.csv"

    _write_semantic(
        semantic,
        [_row(1, "example", "Soporte remoto para backup de 100GB en Windows 11", 35000)],
    )

    _, remote = build_pricing_statistics(
        semantic,
        local_out_path=local_out,
        remote_out_path=remote_out,
    )

    assert len(remote) == 1
    assert remote[0]["price_scope"] == "UNKNOWN"
    assert remote[0]["commercial_context"] == "UNKNOWN"


def test_stats_csv_persists_scope_dimensions(tmp_path):
    semantic = tmp_path / "semantic.csv"
    local_out = tmp_path / "local.csv"
    remote_out = tmp_path / "remote.csv"

    _write_semantic(
        semantic,
        [_row(1, "example", "Hora servicio técnico remoto", 40000)],
    )

    build_pricing_statistics(
        semantic,
        local_out_path=local_out,
        remote_out_path=remote_out,
    )

    with remote_out.open("r", encoding="utf-8-sig", newline="") as f:
        row = next(csv.DictReader(f))

    assert row["price_scope"] == "PER_HOUR"
    assert row["commercial_context"] == "UNKNOWN"
