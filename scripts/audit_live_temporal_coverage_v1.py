from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - project currently depends on bs4
    BeautifulSoup = None


SCHEMA_VERSION = "live-temporal-coverage-audit-v1"

STRUCTURED_FIELDS = (
    "datePublished",
    "dateModified",
    "validFrom",
    "validThrough",
    "uploadDate",
)

SPANISH_MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)

MONTH_YEAR_RE = re.compile(
    rf"\b(?:{'|'.join(SPANISH_MONTHS)})\s+(?:de\s+)?20\d{{2}}\b",
    re.IGNORECASE,
)
NUMERIC_DATE_RE = re.compile(
    r"\b(?:[0-3]?\d[/-][01]?\d[/-]20\d{2}|20\d{2}-[01]\d-[0-3]\d)\b"
)
ISO_DATETIME_RE = re.compile(
    r"\b20\d{2}-[01]\d-[0-3]\d[T ][0-2]\d:[0-5]\d"
)

VALIDITY_PATTERNS = (
    r"\bvigente(?:s)?\b",
    r"\bvigencia\b",
    r"\bv[aá]lid[oa]s?\b",
    r"\bv[aá]lid[oa]\s+hasta\b",
    r"\bhasta\s+el\b",
    r"\bhasta\s+agotar\s+stock\b",
    r"\bprecio(?:s)?\s+actualizad[oa]s?\b",
    r"\bactualizad[oa]\b",
    r"\b[uú]ltima\s+actualizaci[oó]n\b",
    r"\bdesde\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
    r"septiembre|octubre|noviembre|diciembre)\b",
)
VALIDITY_RE = re.compile("|".join(VALIDITY_PATTERNS), re.IGNORECASE)

GENERIC_TEMPORAL_RE = re.compile(
    "|".join(
        (
            MONTH_YEAR_RE.pattern,
            NUMERIC_DATE_RE.pattern,
            ISO_DATETIME_RE.pattern,
            VALIDITY_RE.pattern,
        )
    ),
    re.IGNORECASE,
)

STRUCTURED_DATE_RE = re.compile(
    r'["\'](?P<field>'
    + "|".join(STRUCTURED_FIELDS)
    + r')["\']\s*:\s*["\'](?P<value>[^"\']+)["\']',
    re.IGNORECASE,
)

TIME_TAG_RE = re.compile(
    r"<time\b[^>]*\bdatetime\s*=\s*[\"']([^\"']+)[\"'][^>]*>",
    re.IGNORECASE,
)


def _fold(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.casefold().split())


def _visible_text(html: str) -> str:
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for node in soup(["script", "style", "noscript"]):
            node.decompose()
        return " ".join(soup.get_text(" ", strip=True).split())
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def _structured_candidates(raw_html: str) -> tuple[str, ...]:
    values = {
        f"{match.group('field')}={match.group('value').strip()}"
        for match in STRUCTURED_DATE_RE.finditer(raw_html)
    }
    values.update(
        f"time.datetime={value.strip()}"
        for value in TIME_TAG_RE.findall(raw_html)
        if value.strip()
    )
    return tuple(sorted(values))


def _text_candidates(text: str) -> tuple[str, ...]:
    values = set()
    for regex in (MONTH_YEAR_RE, NUMERIC_DATE_RE, ISO_DATETIME_RE):
        values.update(match.group(0).strip() for match in regex.finditer(text))
    return tuple(sorted(values))


def _validity_candidates(text: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                match.group(0).strip()
                for match in VALIDITY_RE.finditer(text)
                if match.group(0).strip()
            }
        )
    )


def _offer_window(
    visible_text: str,
    economic_object_raw: object,
    *,
    radius: int = 420,
) -> str:
    target = _fold(economic_object_raw)
    folded_text = _fold(visible_text)
    if not target:
        return ""

    position = folded_text.find(target)
    if position < 0:
        # Conservative fallback for formatting differences:
        # use the first 48 chars of the folded economic object only if
        # sufficiently distinctive.
        prefix = target[:48].strip()
        if len(prefix) < 24:
            return ""
        position = folded_text.find(prefix)
        if position < 0:
            return ""

    start = max(0, position - radius)
    end = min(len(folded_text), position + len(target) + radius)
    return folded_text[start:end]


def _discover_databases(live_root: Path, mode: str) -> list[Path]:
    candidates = sorted(
        path
        for path in live_root.glob("*/enki_pricing.db")
        if path.is_file()
    )
    if not candidates:
        candidates = sorted(
            path
            for path in live_root.rglob("enki_pricing.db")
            if path.is_file()
        )
    if not candidates:
        raise SystemExit(f"No enki_pricing.db found under {live_root}")

    if mode == "all":
        return candidates

    # Run ids are timestamp-shaped in the canonical runner, so lexical parent
    # ordering is deterministic. Fall back to path string if nested differently.
    return [max(candidates, key=lambda value: str(value.parent))]


def _read_rows(db_path: Path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        documents = {
            int(row["id"]): row
            for row in connection.execute(
                """
                SELECT
                    id,
                    source,
                    source_record_id,
                    source_url,
                    retrieved_at,
                    content_type,
                    raw_content,
                    content_hash,
                    metadata_json
                FROM raw_documents
                ORDER BY id
                """
            )
        }
        observations = list(
            connection.execute(
                """
                SELECT
                    id,
                    raw_document_id,
                    source,
                    source_record_id,
                    source_url,
                    extractor_version,
                    extraction_status,
                    economic_object_raw_json,
                    price_raw_json,
                    price_value_json,
                    currency_raw_json,
                    metadata_json
                FROM commercial_price_observations
                ORDER BY id
                """
            )
        )
    finally:
        connection.close()
    return documents, observations


def _json_value(raw: object):
    try:
        return json.loads(str(raw))
    except (TypeError, json.JSONDecodeError):
        return raw


def audit_database(db_path: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    documents, observations = _read_rows(db_path)

    document_cache: dict[int, dict[str, object]] = {}
    for document_id, row in documents.items():
        raw_html = str(row["raw_content"] or "")
        visible = _visible_text(raw_html)
        document_cache[document_id] = {
            "row": row,
            "visible_text": visible,
            "structured": _structured_candidates(raw_html),
            "text_dates": _text_candidates(visible),
            "validity": _validity_candidates(visible),
        }

    records: list[dict[str, object]] = []
    counters = Counter()

    for observation in observations:
        counters["observations_total"] += 1

        observation_id = str(observation["id"])
        raw_document_fk = int(observation["raw_document_id"])
        document = document_cache.get(raw_document_fk)

        if document is None:
            counters["missing_raw_fk"] += 1
            records.append(
                {
                    "run": db_path.parent.name,
                    "db_path": str(db_path),
                    "observation_id": observation_id,
                    "source": observation["source"],
                    "raw_document_fk": raw_document_fk,
                    "raw_document_hash": "",
                    "acquired_at": "",
                    "economic_object_raw": _json_value(
                        observation["economic_object_raw_json"]
                    ),
                    "document_structured_candidates": "",
                    "document_text_date_candidates": "",
                    "document_validity_candidates": "",
                    "offer_adjacent_date_candidates": "",
                    "offer_adjacent_validity_candidates": "",
                    "offer_window_found": "NO",
                    "temporal_identity_candidate": "NO",
                    "current_reproducible": "NO",
                    "notes": "BROKEN_RAW_FK",
                }
            )
            continue

        raw = document["row"]
        visible = str(document["visible_text"])
        economic_object = _json_value(
            observation["economic_object_raw_json"]
        )
        window = _offer_window(visible, economic_object)

        structured = tuple(document["structured"])
        document_dates = tuple(document["text_dates"])
        document_validity = tuple(document["validity"])
        adjacent_dates = _text_candidates(window) if window else ()
        adjacent_validity = _validity_candidates(window) if window else ()

        acquired_at = str(raw["retrieved_at"] or "").strip()

        if acquired_at:
            counters["acquired_at_known"] += 1
        if structured:
            counters["document_structured_signal"] += 1
        if document_dates:
            counters["document_text_date_signal"] += 1
        if document_validity:
            counters["document_validity_signal"] += 1
        if window:
            counters["offer_window_found"] += 1
        if adjacent_dates:
            counters["offer_adjacent_date_signal"] += 1
        if adjacent_validity:
            counters["offer_adjacent_validity_signal"] += 1
        if adjacent_dates or adjacent_validity:
            counters["offer_adjacent_any_temporal_signal"] += 1

        # This is intentionally only a candidate flag. It does not satisfy the
        # current-pricing gate and MUST NOT be interpreted as freshness policy.
        temporal_identity_candidate = bool(
            acquired_at and raw["content_hash"]
        )
        if temporal_identity_candidate:
            counters["temporal_identity_candidate"] += 1

        records.append(
            {
                "run": db_path.parent.name,
                "db_path": str(db_path),
                "observation_id": observation_id,
                "source": observation["source"],
                "raw_document_fk": raw_document_fk,
                "raw_document_hash": raw["content_hash"],
                "acquired_at": acquired_at,
                "economic_object_raw": economic_object,
                "document_structured_candidates": " | ".join(structured),
                "document_text_date_candidates": " | ".join(document_dates),
                "document_validity_candidates": " | ".join(document_validity),
                "offer_adjacent_date_candidates": " | ".join(adjacent_dates),
                "offer_adjacent_validity_candidates": " | ".join(
                    adjacent_validity
                ),
                "offer_window_found": "YES" if window else "NO",
                "temporal_identity_candidate": (
                    "YES" if temporal_identity_candidate else "NO"
                ),
                # Audit only. No live freshness policy exists in this script.
                "current_reproducible": "NO",
                "notes": "",
            }
        )

    summary = {
        "run": db_path.parent.name,
        "db_path": str(db_path),
        "raw_documents_total": len(documents),
        **dict(counters),
    }
    return records, summary


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "run",
        "db_path",
        "observation_id",
        "source",
        "raw_document_fk",
        "raw_document_hash",
        "acquired_at",
        "economic_object_raw",
        "document_structured_candidates",
        "document_text_date_candidates",
        "document_validity_candidates",
        "offer_adjacent_date_candidates",
        "offer_adjacent_validity_candidates",
        "offer_window_found",
        "temporal_identity_candidate",
        "current_reproducible",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only audit of temporal signals already present in Enki live "
            "SQLite evidence. This tool never promotes evidence to CURRENT."
        )
    )
    parser.add_argument("--live-root", default="data/live")
    parser.add_argument(
        "--mode",
        choices=("latest", "all"),
        default="latest",
    )
    parser.add_argument(
        "--out-dir",
        default="data/live_diagnostics/temporal_coverage_v1",
    )
    args = parser.parse_args()

    live_root = Path(args.live_root)
    databases = _discover_databases(live_root, args.mode)

    all_rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []

    for database in databases:
        rows, summary = audit_database(database)
        all_rows.extend(rows)
        summaries.append(summary)

    aggregate = Counter()
    for summary in summaries:
        for key, value in summary.items():
            if key in {"run", "db_path"}:
                continue
            if isinstance(value, int):
                aggregate[key] += value

    payload = {
        "schema_version": SCHEMA_VERSION,
        "mode": args.mode,
        "live_root": str(live_root),
        "databases": [str(path) for path in databases],
        "runs": summaries,
        "aggregate": dict(sorted(aggregate.items())),
        "interpretation": {
            "acquired_at": (
                "Acquisition provenance only; never price validity by itself."
            ),
            "document_temporal_signal": (
                "Candidate page-level temporal context; not offer applicability."
            ),
            "offer_adjacent_temporal_signal": (
                "Candidate evidence near the observed economic object; requires "
                "manual/contract validation before any temporal projection."
            ),
            "current_reproducible": (
                "Always NO in this audit. No freshness policy is invented."
            ),
        },
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / f"temporal_coverage_{args.mode}.csv"
    json_path = out_dir / f"temporal_coverage_{args.mode}.summary.json"

    _write_csv(csv_path, all_rows)
    json_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("ENKI LIVE TEMPORAL COVERAGE AUDIT v1")
    print("====================================")
    print(f"Mode:              {args.mode}")
    print(f"Databases:         {len(databases)}")
    print(f"Raw documents:     {aggregate['raw_documents_total']}")
    print(f"Observations:      {aggregate['observations_total']}")
    print(f"Acquired known:    {aggregate['acquired_at_known']}")
    print(
        "Structured date:   "
        f"{aggregate['document_structured_signal']}"
    )
    print(
        "Document dates:    "
        f"{aggregate['document_text_date_signal']}"
    )
    print(
        "Document validity: "
        f"{aggregate['document_validity_signal']}"
    )
    print(
        "Offer windows:     "
        f"{aggregate['offer_window_found']}"
    )
    print(
        "Offer-adj dates:   "
        f"{aggregate['offer_adjacent_date_signal']}"
    )
    print(
        "Offer-adj validity:"
        f" {aggregate['offer_adjacent_validity_signal']}"
    )
    print(
        "Offer temporal any:"
        f" {aggregate['offer_adjacent_any_temporal_signal']}"
    )
    print("CURRENT admitted:  0 (audit never promotes)")
    print()
    print(f"CSV:     {csv_path}")
    print(f"Summary: {json_path}")


if __name__ == "__main__":
    main()
