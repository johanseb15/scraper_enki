import json
from datetime import datetime
from pathlib import Path

from src.dominio.evidencia import ConsultaUsuarioRaw


CORPUS = (
    Path(__file__).resolve().parents[1]
    / "data/language/observed_user_raw_v1.jsonl"
)
EXPECTED_SOURCE_IDS = (
    "1rb6392",
    "1rdxemu",
    "1sobhdz",
    "14trhq2",
    "1royli3",
    "1wmr648",
)


def test_loader_preserves_six_observed_user_raw_rows_in_order():
    rows = [
        json.loads(line)
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 6

    from src.infraestructura.observed_user_raw_corpus import (
        load_observed_user_raw_corpus,
    )

    records = load_observed_user_raw_corpus(CORPUS)

    assert isinstance(records, tuple)
    assert len(records) == 6
    assert tuple(record.source_id for record in records) == EXPECTED_SOURCE_IDS

    for row, record in zip(rows, records, strict=True):
        assert type(record) is ConsultaUsuarioRaw
        for field in ("source", "source_id", "source_url", "raw_text", "language"):
            assert getattr(record, field) == row[field]
        assert type(record.observed_at) is datetime
        assert record.observed_at == datetime.fromisoformat(row["observed_at"])
        assert record.metadata == row["metadata"]
        assert record.metadata["published_at"] == row["metadata"]["published_at"]
        assert record.metadata["capture_method"] == "indexed_public_source"
        assert record.metadata["source_access_direct"] is False
        assert record.metadata["literal_verified"] is True
        assert record.metadata.get("case_origin") != "HUMAN_REAL"

    web_real_002 = next(
        record
        for record in records
        if record.metadata["legacy_case_id"] == "WEB_REAL_002"
    )
    assert web_real_002.metadata["raw_record_scope"] == "post_only"
    assert (
        web_real_002.metadata["legacy_case_scope"]
        == "post_plus_followup_comment"
    )
