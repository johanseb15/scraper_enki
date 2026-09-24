import json
from datetime import datetime
from pathlib import Path


CORPUS = (
    Path(__file__).resolve().parents[1]
    / "data/language/observed_user_raw_v1.jsonl"
)
EXPECTED_LEGACY_CASE_IDS = {
    f"WEB_REAL_{number:03d}" for number in range(1, 7)
}
EXPECTED_SOURCES = {
    "WEB_REAL_001": ("1rb6392", "AskArgentina", "2026-02-21"),
    "WEB_REAL_002": ("1rdxemu", "AskArgentina", "2026-02-25"),
    "WEB_REAL_003": ("1sobhdz", "PcGamerArgentina", "2026-04-17"),
    "WEB_REAL_004": ("14trhq2", "AskArgentina", "2023-07-08"),
    "WEB_REAL_005": ("1royli3", "ArgamingConsultas", "2026-03-09"),
    "WEB_REAL_006": ("1wmr648", "PcGamerArgentina", "2026-09-21"),
}


def test_observed_user_raw_v1_has_six_traceable_reddit_posts():
    assert CORPUS.is_file(), f"Missing RAW corpus: {CORPUS}"

    rows = [
        json.loads(line)
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 6

    source_ids = []
    legacy_case_ids = []
    for row in rows:
        assert isinstance(row, dict)
        assert row["source"] == "reddit"
        assert row.get("case_origin") != "HUMAN_REAL"

        for field in ("source_id", "source_url", "raw_text"):
            assert isinstance(row[field], str) and row[field].strip()
        assert row["language"] == "es"
        assert isinstance(row["observed_at"], str)
        datetime.fromisoformat(row["observed_at"])

        metadata = row["metadata"]
        assert isinstance(metadata, dict)
        assert isinstance(metadata["published_at"], str)
        datetime.fromisoformat(metadata["published_at"])
        assert metadata["source_type"] == "community"
        assert metadata["capture_method"] == "indexed_public_source"
        assert metadata["source_access_direct"] is False
        assert metadata["literal_verified"] is True
        for field in ("subreddit", "legacy_case_id"):
            assert isinstance(metadata[field], str) and metadata[field].strip()
        assert metadata["content_kind"] == "post"
        assert metadata["raw_text_composition"] == "title_blankline_selftext_v1"

        expected_source_id, expected_subreddit, expected_published_at = (
            EXPECTED_SOURCES[metadata["legacy_case_id"]]
        )
        assert row["source_id"] == expected_source_id
        assert metadata["subreddit"] == expected_subreddit
        assert metadata["published_at"] == expected_published_at

        if metadata["legacy_case_id"] == "WEB_REAL_002":
            assert metadata["raw_record_scope"] == "post_only"
            assert metadata["legacy_case_scope"] == "post_plus_followup_comment"

        source_ids.append(row["source_id"])
        legacy_case_ids.append(metadata["legacy_case_id"])

    assert len(set(source_ids)) == 6
    assert len(set(legacy_case_ids)) == 6
    assert set(legacy_case_ids) == EXPECTED_LEGACY_CASE_IDS
