import csv
import json
from pathlib import Path

from scripts.build_semantic_understanding import (
    build_semantic_understanding_artifact,
)


def _row(
    observation_id,
    raw_expression,
    semantic_role,
    *,
    canonical_service="",
    matched_services="",
):
    return {
        "observation_id": observation_id,
        "economic_object_raw": raw_expression,
        "semantic_role": semantic_role,
        "market_scope": "UNKNOWN",
        "source": "provider_a",
        "provider": "Provider A",
        "province": "Córdoba",
        "canonical_service": canonical_service,
        "matched_services": matched_services,
    }


def _write_input(path: Path, rows):
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_artifact_preserves_cardinality_status_and_provenance(tmp_path):
    input_path = tmp_path / "semantic_normalization.csv"
    output_path = tmp_path / "semantic_understanding.csv"

    _write_input(
        input_path,
        [
            _row(
                "1",
                "instalación de Windows",
                "SINGLE_SERVICE",
                canonical_service="INSTALACION_SO",
            ),
            _row("2", "Desde", "NON_OBJECT"),
            _row("3", "*", "NON_OBJECT"),
        ],
    )

    result = build_semantic_understanding_artifact(
        input_path,
        output_path,
        interpretation_version="test-v1",
    )

    assert result == output_path
    with output_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 3
    assert [row["understanding_status"] for row in rows] == [
        "FULLY_REPRESENTED",
        "PARTIALLY_UNDERSTOOD",
        "UNKNOWN",
    ]
    assert rows[0]["meaning_type"] == ""
    assert rows[1]["meaning_type"] == "NonObjectMeaning"

    observation_provenance = json.loads(rows[1]["observation_provenance_json"])
    interpretation_provenance = json.loads(rows[1]["interpretation_provenance_json"])

    assert observation_provenance["origin_type"] == "COMMERCIAL_OBSERVATION"
    assert interpretation_provenance["origin_type"] == "SEMANTIC_NORMALIZATION"
    assert interpretation_provenance["origin_version"] == "test-v1"


def test_artifact_serializes_typed_meaning_without_mutating_source(tmp_path):
    input_path = tmp_path / "semantic_normalization.csv"
    output_path = tmp_path / "semantic_understanding.csv"

    source_rows = [_row("1", "$0,00", "NON_OBJECT")]
    _write_input(input_path, source_rows)
    before = input_path.read_bytes()

    build_semantic_understanding_artifact(input_path, output_path)

    assert input_path.read_bytes() == before

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))

    meaning = json.loads(row["meaning_json"])
    assert row["meaning_type"] == "NonObjectMeaning"
    assert meaning["meaning_kind"] == "ZERO_VALUE_PLACEHOLDER"
    assert "DO_NOT_OVERRIDE_OBSERVED_PRICE" in meaning["signals"]


def test_artifact_output_is_deterministic(tmp_path):
    input_path = tmp_path / "semantic_normalization.csv"
    output_a = tmp_path / "a.csv"
    output_b = tmp_path / "b.csv"

    _write_input(
        input_path,
        [
            _row("1", "Desde", "NON_OBJECT"),
            _row("2", "DISPONIBLE", "NON_OBJECT"),
        ],
    )

    build_semantic_understanding_artifact(input_path, output_a)
    build_semantic_understanding_artifact(input_path, output_b)

    assert output_a.read_bytes() == output_b.read_bytes()


def test_artifact_has_no_pricing_decision_fields(tmp_path):
    input_path = tmp_path / "semantic_normalization.csv"
    output_path = tmp_path / "semantic_understanding.csv"

    _write_input(input_path, [_row("1", "Desde", "NON_OBJECT")])
    build_semantic_understanding_artifact(input_path, output_path)

    header = output_path.read_text(encoding="utf-8").splitlines()[0]

    assert "decision_label" not in header
    assert "recommended_price" not in header
    assert "price_value" not in header
