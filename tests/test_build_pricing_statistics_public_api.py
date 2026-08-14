import csv
from pathlib import Path

from scripts.build_pricing_statistics import build_pricing_statistics


FIELDS = [
    "observation_id", "source", "province", "city", "economic_object_raw",
    "price_value", "currency", "semantic_role", "market_scope",
    "matched_services", "canonical_service", "comparability_key",
    "original_comparable_status", "extractor_version",
]


def _write_semantic(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def test_build_pricing_statistics_public_api(tmp_path):
    normalization = tmp_path / "semantic.csv"
    local_out = tmp_path / "local.csv"
    remote_out = tmp_path / "remote.csv"

    base = {
        "observation_id": "1",
        "source": "provider_a",
        "province": "Córdoba",
        "city": "Córdoba",
        "economic_object_raw": "Formateo",
        "price_value": "50000",
        "currency": "ARS",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "LOCAL_SERVICE",
        "matched_services": "FORMATEO_INSTALACION_SO",
        "canonical_service": "FORMATEO_INSTALACION_SO",
        "comparability_key": "Córdoba::FORMATEO_INSTALACION_SO",
        "original_comparable_status": "INDETERMINATE",
        "extractor_version": "generic_price_extractor_v3",
    }
    remote = dict(base)
    remote.update({
        "observation_id": "2",
        "source": "provider_b",
        "province": "CABA",
        "economic_object_raw": "Soporte remoto",
        "price_value": "35000",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "matched_services": "SOPORTE_REMOTO",
        "canonical_service": "SOPORTE_REMOTO",
        "comparability_key": "AR::SOPORTE_REMOTO",
    })

    _write_semantic(normalization, [base, remote])

    local, remote_rows = build_pricing_statistics(
        normalization,
        local_out_path=local_out,
        remote_out_path=remote_out,
    )

    assert len(local) == 1
    assert local[0]["market"] == "Córdoba"
    assert local[0]["canonical_service"] == "FORMATEO_INSTALACION_SO"
    assert len(remote_rows) == 1
    assert remote_rows[0]["market"] == "AR"
    assert remote_rows[0]["canonical_service"] == "SOPORTE_REMOTO"
    assert local_out.exists()
    assert remote_out.exists()
