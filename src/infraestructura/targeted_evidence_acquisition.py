from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests

from src.infraestructura.downloader import DEFAULT_HEADERS


def acquire_planned_sources(
    plan_path: str | Path,
    historical_manifest_path: str | Path,
    raw_root: str | Path,
    acquisition_manifest_path: str | Path,
    *,
    session: requests.Session | None = None,
    now: Callable[[], datetime] | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    actions = [json.loads(line) for line in Path(plan_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    unique = {}
    for action in actions:
        unique.setdefault((action["source"], action["source_url"]), action)
    historical = _historical_hashes(historical_manifest_path)
    client = session or requests.Session()
    clock = now or (lambda: datetime.now(timezone.utc))
    output_rows = []
    root = Path(raw_root)
    for (source, url), action in sorted(unique.items()):
        acquired_at = clock().astimezone(timezone.utc).isoformat()
        try:
            response = client.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            status_code = int(response.status_code)
            if status_code in {403, 429}:
                output_rows.append(_failure(source, url, acquired_at, "BLOCKED", status_code, f"HTTP_{status_code}"))
                continue
            response.raise_for_status()
            content = response.content
            digest = hashlib.sha256(content).hexdigest()
            previous = historical.get((source, url), set())
            change_status = "UNCHANGED" if digest in previous else "CHANGED" if previous else "NEW"
            suffix = ".html" if "html" in response.headers.get("Content-Type", "").casefold() else ".raw"
            relative = Path(source) / f"{digest}{suffix}"
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            metadata_path = path.with_suffix(path.suffix + ".metadata.json")
            metadata = {
                "schema_version": "targeted-raw-acquisition-v1",
                "source": source,
                "source_url": url,
                "acquired_at": acquired_at,
                "content_hash": digest,
                "content_length": len(content),
                "content_type": response.headers.get("Content-Type"),
                "http_status": status_code,
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "extractor_version": "selective-near-comparable-acquisition-v1",
                "change_status": change_status,
            }
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            output_rows.append({
                **metadata,
                "status": "SUCCEEDED",
                "raw_document_reference": str(path).replace("\\", "/"),
                "metadata_reference": str(metadata_path).replace("\\", "/"),
            })
        except requests.RequestException as exc:
            output_rows.append(_failure(source, url, acquired_at, "UNAVAILABLE", None, type(exc).__name__))
    _write_jsonl(acquisition_manifest_path, output_rows)
    return {
        "NETWORK_REQUESTS": len(unique),
        "SOURCES_ATTEMPTED": len(unique),
        "SOURCES_SUCCEEDED": sum(row["status"] == "SUCCEEDED" for row in output_rows),
        "SOURCES_FAILED": sum(row["status"] in {"UNAVAILABLE", "FAILED"} for row in output_rows),
        "BLOCKED": sum(row["status"] == "BLOCKED" for row in output_rows),
        "UNCHANGED_CONTENT": sum(row.get("change_status") == "UNCHANGED" for row in output_rows),
        "CHANGED_CONTENT": sum(row.get("change_status") == "CHANGED" for row in output_rows),
        "NEW_CONTENT": sum(row.get("change_status") == "NEW" for row in output_rows),
        "NEW_RAW_DOCUMENTS": sum(row["status"] == "SUCCEEDED" for row in output_rows),
    }


def _historical_hashes(path):
    result = {}
    manifest = Path(path)
    if not manifest.exists():
        return result
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            raw_path = Path(row["raw_path"])
            if raw_path.exists():
                digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
                result.setdefault((row["source"], row["source_url"]), set()).add(digest)
    return result


def _failure(source, url, acquired_at, status, http_status, reason):
    return {
        "schema_version": "targeted-raw-acquisition-v1",
        "source": source,
        "source_url": url,
        "acquired_at": acquired_at,
        "status": status,
        "http_status": http_status,
        "reason": reason,
        "change_status": status,
        "raw_document_reference": None,
        "extractor_version": "selective-near-comparable-acquisition-v1",
    }


def _write_jsonl(path, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
