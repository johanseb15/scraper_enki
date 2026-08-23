from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterable

from src.dominio.temporal_evidence import TemporalEvidence, TemporalEvidenceState
from src.infraestructura.offer_evidence_artifact import load_offer_evidence_sidecar


SCHEMA_VERSION = "temporal-evidence-v1"
_MONTH_PATTERN = re.compile(
    r"\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|"
    r"octubre|noviembre|diciembre)\s+(20\d{2})\b",
    re.IGNORECASE,
)


def _jsonl(path: str | Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _valid_iso_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _raw_price_time(path: Path) -> tuple[str | None, tuple[str, ...]]:
    if not path.is_file():
        return None, ()
    text = path.read_text(encoding="utf-8")
    values = tuple(
        sorted(
            {
                f"{match.group(1).casefold()} {match.group(2)}"
                for match in _MONTH_PATTERN.finditer(text)
            }
        )
    )
    return (values[0] if len(values) == 1 else None), values


def build_temporal_evidence(
    repository_root: str | Path,
    *,
    normalization_path: str | Path,
    offer_evidence_path: str | Path,
    identities_path: str | Path,
    acquisition_manifest_path: str | Path,
) -> dict[str, TemporalEvidence]:
    root = Path(repository_root).resolve()
    with Path(normalization_path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    offers = load_offer_evidence_sidecar(offer_evidence_path)
    identities = {
        str(item["observation_id"]): item
        for item in _jsonl(identities_path)
        if item.get("status") == "RESOLVED"
    }

    acquisitions: dict[str, list[dict[str, object]]] = {}
    for item in _jsonl(acquisition_manifest_path):
        raw_id = f"sha256:{item['content_hash']}"
        raw_path = (root / str(item["raw_document_reference"])).resolve()
        try:
            raw_path.relative_to(root)
        except ValueError:
            continue
        if not raw_path.is_file():
            continue
        digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        if digest != item["content_hash"]:
            continue
        acquired_at = str(item.get("acquired_at") or "")
        if not acquired_at or not _valid_iso_timestamp(acquired_at):
            continue
        acquisitions.setdefault(raw_id, []).append(item)

    raw_price_times: dict[str, tuple[str | None, tuple[str, ...]]] = {}
    result: dict[str, TemporalEvidence] = {}
    for row in rows:
        observation_id = row["observation_id"]
        offer = offers.get(observation_id)
        lineage = offer.lineage if offer else None
        identity = identities.get(observation_id)
        identity_raw_id = str(identity["raw_document_id"]) if identity else None
        candidates: list[tuple[str, str, str]] = []
        if lineage and lineage.acquired_at and _valid_iso_timestamp(lineage.acquired_at):
            candidates.append(
                (
                    lineage.acquired_at,
                    lineage.raw_document_id or "UNKNOWN",
                    f"{offer_evidence_path}#{observation_id}",
                )
            )
        if identity_raw_id:
            for manifest in acquisitions.get(identity_raw_id, ()):
                candidates.append(
                    (
                        str(manifest["acquired_at"]),
                        identity_raw_id,
                        str(manifest["metadata_reference"]),
                    )
                )

        unique_times = sorted({item[0] for item in candidates})
        conflicts: list[str] = []
        if len(unique_times) > 1:
            conflicts.append("MULTIPLE_ACQUISITION_TIMES_WITHOUT_SNAPSHOT_IDENTITY")

        price_time = None
        if lineage and lineage.raw_document_path:
            raw_path = (root / lineage.raw_document_path).resolve()
            key = lineage.raw_document_id or lineage.raw_document_path
            if key not in raw_price_times:
                raw_price_times[key] = _raw_price_time(raw_path)
            price_time, raw_values = raw_price_times[key]
            if len(raw_values) > 1:
                conflicts.append("MULTIPLE_RAW_PRICE_TIME_CONTEXTS")

        acquired_at = unique_times[0] if len(unique_times) == 1 else None
        if conflicts:
            state = TemporalEvidenceState.TEMPORAL_CONFLICT
        elif acquired_at:
            state = TemporalEvidenceState.HISTORICAL_REPRODUCIBLE
        else:
            state = TemporalEvidenceState.TEMPORAL_UNKNOWN
        provenance = tuple(sorted({item[2] for item in candidates}))
        if price_time and lineage and lineage.raw_document_path:
            provenance = tuple(sorted((*provenance, lineage.raw_document_path)))

        result[observation_id] = TemporalEvidence(
            observation_id=observation_id,
            source_id=row.get("source") or None,
            extractor_version=row.get("extractor_version") or None,
            raw_document_id=(identity_raw_id or (lineage.raw_document_id if lineage else None)),
            acquired_at=acquired_at,
            price_validity_time_raw=price_time,
            temporal_state=state,
            temporal_identity_known=bool(acquired_at and identity_raw_id),
            freshness_policy_known=False,
            provenance=provenance,
            conflicts=tuple(conflicts),
            filesystem_dates_used_as_evidence=False,
        )
    return result


def write_temporal_evidence(
    path: str | Path,
    evidence: Iterable[TemporalEvidence],
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for item in sorted(evidence, key=lambda value: int(value.observation_id)):
            payload = {"schema_version": SCHEMA_VERSION, **_jsonable(item)}
            handle.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )


def load_temporal_evidence(path: str | Path) -> dict[str, TemporalEvidence]:
    result: dict[str, TemporalEvidence] = {}
    for line_number, payload in enumerate(_jsonl(path), 1):
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported temporal evidence schema at line {line_number}.")
        observation_id = str(payload.get("observation_id") or "")
        if not observation_id or observation_id in result:
            raise ValueError(f"Invalid temporal observation at line {line_number}.")
        result[observation_id] = TemporalEvidence(
            observation_id=observation_id,
            source_id=payload.get("source_id"),
            extractor_version=payload.get("extractor_version"),
            raw_document_id=payload.get("raw_document_id"),
            acquired_at=payload.get("acquired_at"),
            published_at=payload.get("published_at"),
            observed_at=payload.get("observed_at"),
            valid_from=payload.get("valid_from"),
            valid_to=payload.get("valid_to"),
            price_validity_time_raw=payload.get("price_validity_time_raw"),
            extractor_run_at=payload.get("extractor_run_at"),
            temporal_state=TemporalEvidenceState(str(payload["temporal_state"])),
            temporal_identity_known=bool(payload.get("temporal_identity_known")),
            freshness_policy_known=bool(payload.get("freshness_policy_known")),
            freshness_policy_version=payload.get("freshness_policy_version"),
            provenance=tuple(payload.get("provenance", ())),
            conflicts=tuple(payload.get("conflicts", ())),
            filesystem_dates_used_as_evidence=bool(
                payload.get("filesystem_dates_used_as_evidence")
            ),
        )
    return result


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value
