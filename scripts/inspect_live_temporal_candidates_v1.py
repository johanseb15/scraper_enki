from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


SCHEMA_VERSION = "live-temporal-candidate-inspection-v1"

STRUCTURED_FIELD_RE = re.compile(
    r"(?P<field>datePublished|dateModified|validFrom|validThrough|uploadDate|time\.datetime)=",
    re.IGNORECASE,
)

TEMPORAL_TOKEN_RE = re.compile(
    r"(?i)\b(?:"
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|"
    r"octubre|noviembre|diciembre|"
    r"vigente|vigencia|v[aá]lid[oa]|actualizad[oa]|"
    r"20\d{2}-[01]\d-[0-3]\d|"
    r"[0-3]?\d[/-][01]?\d[/-]20\d{2}"
    r")\b"
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_raw_document(db_path: Path, raw_document_fk: int) -> dict[str, str] | None:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            """
            SELECT
                id,
                source,
                source_url,
                retrieved_at,
                content_hash,
                raw_content
            FROM raw_documents
            WHERE id = ?
            """,
            (raw_document_fk,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return {
        "id": str(row["id"]),
        "source": str(row["source"]),
        "source_url": str(row["source_url"]),
        "retrieved_at": str(row["retrieved_at"]),
        "content_hash": str(row["content_hash"]),
        "raw_content": str(row["raw_content"]),
    }


def _plain_text(html: str) -> str:
    text = re.sub(r"(?is)<script\b.*?</script>", " ", html)
    text = re.sub(r"(?is)<style\b.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return " ".join(text.split())


def _snippet(text: str, needles: list[str], radius: int = 220) -> str:
    lowered = text.casefold()

    positions = []
    for needle in needles:
        token = (needle or "").strip()
        if not token:
            continue
        pos = lowered.find(token.casefold())
        if pos >= 0:
            positions.append(pos)

    temporal_match = TEMPORAL_TOKEN_RE.search(text)
    if temporal_match is not None:
        positions.append(temporal_match.start())

    if not positions:
        return ""

    center = min(positions)
    start = max(0, center - radius)
    end = min(len(text), center + radius)

    return text[start:end].strip()


def _structured_fields(raw: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                match.group("field")
                for match in STRUCTURED_FIELD_RE.finditer(raw or "")
            }
        )
    )


def _triage(row: dict[str, str], structured_fields: tuple[str, ...]) -> str:
    has_offer_date = bool((row.get("offer_adjacent_date_candidates") or "").strip())
    has_offer_validity = bool(
        (row.get("offer_adjacent_validity_candidates") or "").strip()
    )
    strong_structured = any(
        field.casefold() in {"validfrom", "validthrough"}
        for field in structured_fields
    )
    page_update_structured = any(
        field.casefold() in {"datemodified", "datepublished", "uploaddate"}
        for field in structured_fields
    )

    if has_offer_validity:
        return "OFFER_ADJACENT_VALIDITY_TEXT"
    if has_offer_date and strong_structured:
        return "OFFER_DATE_PLUS_VALIDITY_STRUCTURED"
    if has_offer_date and page_update_structured:
        return "OFFER_DATE_PLUS_PAGE_DATE_STRUCTURED"
    if has_offer_date:
        return "OFFER_ADJACENT_DATE_ONLY"
    if strong_structured:
        return "VALIDITY_STRUCTURED_ONLY"
    if page_update_structured:
        return "PAGE_DATE_STRUCTURED_ONLY"
    if structured_fields:
        return "TIME_TAG_OR_OTHER_STRUCTURED_ONLY"
    return "NO_RELEVANT_SIGNAL"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only triage of temporal candidates produced by "
            "audit_live_temporal_coverage_v1.py. Never promotes CURRENT."
        )
    )
    parser.add_argument(
        "--coverage",
        default=(
            "data/live_diagnostics/temporal_coverage_v1/"
            "temporal_coverage_latest.csv"
        ),
    )
    parser.add_argument(
        "--out-dir",
        default="data/live_diagnostics/temporal_candidate_inspection_v1",
    )
    args = parser.parse_args()

    coverage_path = Path(args.coverage)
    rows = _read_csv(coverage_path)

    candidates = [
        row
        for row in rows
        if (
            (row.get("offer_adjacent_date_candidates") or "").strip()
            or (row.get("offer_adjacent_validity_candidates") or "").strip()
            or (row.get("document_structured_candidates") or "").strip()
        )
    ]

    raw_cache: dict[tuple[str, int], dict[str, str] | None] = {}
    output_rows: list[dict[str, str]] = []

    triage_counts = Counter()
    source_counts = Counter()
    structured_field_counts = Counter()
    unique_raws_by_triage: dict[str, set[str]] = defaultdict(set)

    for row in candidates:
        db_path = Path(row["db_path"])
        raw_fk = int(row["raw_document_fk"])
        cache_key = (str(db_path), raw_fk)

        if cache_key not in raw_cache:
            raw_cache[cache_key] = _load_raw_document(db_path, raw_fk)

        raw = raw_cache[cache_key]
        raw_html = raw["raw_content"] if raw else ""
        plain = _plain_text(raw_html)

        fields = _structured_fields(
            row.get("document_structured_candidates") or ""
        )
        for field in fields:
            structured_field_counts[field] += 1

        triage = _triage(row, fields)
        triage_counts[triage] += 1
        source_counts[row["source"]] += 1

        raw_identity = (
            f"{db_path}:{raw_fk}:"
            f"{row.get('raw_document_hash') or ''}"
        )
        unique_raws_by_triage[triage].add(raw_identity)

        needles = [
            row.get("economic_object_raw") or "",
            row.get("offer_adjacent_date_candidates") or "",
            row.get("offer_adjacent_validity_candidates") or "",
        ]

        output_rows.append(
            {
                "run": row["run"],
                "observation_id": row["observation_id"],
                "source": row["source"],
                "raw_document_fk": row["raw_document_fk"],
                "raw_document_hash": row["raw_document_hash"],
                "acquired_at": row["acquired_at"],
                "economic_object_raw": row["economic_object_raw"],
                "structured_fields": "|".join(fields),
                "document_structured_candidates": (
                    row.get("document_structured_candidates") or ""
                ),
                "offer_adjacent_date_candidates": (
                    row.get("offer_adjacent_date_candidates") or ""
                ),
                "offer_adjacent_validity_candidates": (
                    row.get("offer_adjacent_validity_candidates") or ""
                ),
                "triage_class": triage,
                "source_url": raw["source_url"] if raw else "",
                "snippet": _snippet(plain, needles),
                "current_reproducible": "NO",
            }
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "temporal_candidates_latest.csv"
    fields = [
        "run",
        "observation_id",
        "source",
        "raw_document_fk",
        "raw_document_hash",
        "acquired_at",
        "economic_object_raw",
        "structured_fields",
        "document_structured_candidates",
        "offer_adjacent_date_candidates",
        "offer_adjacent_validity_candidates",
        "triage_class",
        "source_url",
        "snippet",
        "current_reproducible",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    unique_raws = {
        (
            row["db_path"],
            row["raw_document_fk"],
            row["raw_document_hash"],
        )
        for row in candidates
    }

    payload = {
        "schema_version": SCHEMA_VERSION,
        "coverage_path": str(coverage_path),
        "candidate_observations": len(candidates),
        "candidate_raw_documents": len(unique_raws),
        "triage_counts": dict(sorted(triage_counts.items())),
        "triage_unique_raw_documents": {
            key: len(value)
            for key, value in sorted(unique_raws_by_triage.items())
        },
        "structured_field_counts": dict(
            sorted(structured_field_counts.items())
        ),
        "source_counts": dict(sorted(source_counts.items())),
        "rules": {
            "OFFER_ADJACENT_VALIDITY_TEXT": (
                "Strongest lexical candidate; still not admitted automatically."
            ),
            "OFFER_DATE_PLUS_VALIDITY_STRUCTURED": (
                "Offer-adjacent date plus validFrom/validThrough somewhere in "
                "the same RAW document. Applicability still unproven."
            ),
            "OFFER_DATE_PLUS_PAGE_DATE_STRUCTURED": (
                "Offer-adjacent date plus page publication/update metadata. "
                "Page freshness is not price freshness."
            ),
            "OFFER_ADJACENT_DATE_ONLY": (
                "Date near offer text with no explicit validity semantics."
            ),
            "CURRENT_REPRODUCIBLE": (
                "Always NO. This inspection defines no freshness policy."
            ),
        },
    }

    summary_path = out_dir / "temporal_candidates_latest.summary.json"
    summary_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print("ENKI LIVE TEMPORAL CANDIDATE INSPECTION v1")
    print("==========================================")
    print(f"Candidate observations: {len(candidates)}")
    print(f"Candidate RAW docs:     {len(unique_raws)}")
    print()
    print("TRIAGE")
    print("------")
    for key, count in sorted(
        triage_counts.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        print(
            f"{key}: {count} observations / "
            f"{len(unique_raws_by_triage[key])} RAW docs"
        )
    print()
    print("STRUCTURED FIELDS")
    print("-----------------")
    if structured_field_counts:
        for key, count in sorted(
            structured_field_counts.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            print(f"{key}: {count}")
    else:
        print("none")
    print()
    print("CURRENT admitted: 0 (inspection never promotes)")
    print()
    print(f"CSV:     {csv_path}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
