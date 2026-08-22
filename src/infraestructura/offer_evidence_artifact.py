from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from src.dominio.offer_evidence import (
    EvidenceLineage,
    OfferReachChargedScopeEvidence,
    SourceClaimMethod,
    SourceClaimStatus,
    SourceEconomicClaim,
)
from src.infraestructura.offer_evidence_extractor import (
    EXTRACTOR_VERSION,
    extract_claims_from_explicit_basis,
)
from src.infraestructura.scrapers.generic_price_extractor import (
    extraer_observaciones_precio_genericas,
)


SCHEMA_VERSION = "offer-reach-charged-scope-evidence-v1"


def _identity(source: str, text: str, price: object, currency: str) -> tuple[str, str, str, str]:
    try:
        number = float(str(price))
        normalized_price = str(int(number)) if number.is_integer() else str(number)
    except (TypeError, ValueError):
        normalized_price = str(price or "").strip()
    return source.strip(), text.strip(), normalized_price, currency.strip()


def build_offer_evidence_sidecar(
    normalization_path: str | Path,
    registry_path: str | Path,
    raw_manifest_path: str | Path,
    output_path: str | Path,
    *,
    version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    root = Path.cwd()
    with Path(normalization_path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with Path(registry_path).open(encoding="utf-8-sig", newline="") as handle:
        registry = {row["source"].strip(): row for row in csv.DictReader(handle)}
    with Path(raw_manifest_path).open(encoding="utf-8-sig", newline="") as handle:
        manifest = {row["source"].strip(): row for row in csv.DictReader(handle)}

    ids = [str(row.get("observation_id") or "").strip() for row in rows]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("Offer evidence input requires unique non-empty observation_id values.")

    documents: dict[str, dict[str, str]] = {}
    reproduced: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for source, item in manifest.items():
        path = (root / item["raw_path"]).resolve()
        content = path.read_text(encoding="utf-8")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        raw_document_id = f"sha256:{digest}"
        documents[source] = {
            "path": item["raw_path"].replace("\\", "/"),
            "hash": digest,
            "id": raw_document_id,
            "content": content,
            "acquired_at": item.get("acquired_at", "").strip(),
        }
        registry_row = registry.get(source, {})
        observations = extraer_observaciones_precio_genericas(
            content,
            source=source,
            provider=str(registry_row.get("provider") or "UNKNOWN"),
            source_url=str(item.get("source_url") or registry_row.get("url") or ""),
            raw_document_id=1,
            retrieved_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
            content_hash=digest,
        )
        for observed in observations:
            reproduced[_identity(
                observed.source,
                str(observed.economic_object_raw),
                observed.price_value,
                str(observed.currency_raw),
            )] = documents[source]

    evidence_rows: list[OfferReachChargedScopeEvidence] = []
    reasons: Counter[str] = Counter()
    claim_counts: Counter[str] = Counter()
    provenance_counts: Counter[str] = Counter()
    for row in rows:
        observation_id = row["observation_id"].strip()
        source = row["source"].strip()
        registry_row = registry.get(source, {})
        source_url = str(registry_row.get("url") or "").strip() or None
        key = _identity(source, row["economic_object_raw"], row["price_value"], row["currency"])
        document = reproduced.get(key)
        if document is None:
            reason = (
                "OBSERVATION_NOT_REPRODUCED_FROM_SNAPSHOT"
                if source in documents
                else "SOURCE_RAW_NOT_AVAILABLE"
            )
            reasons[reason] += 1
            lineage = EvidenceLineage(
                observation_id=observation_id,
                source_id=source,
                raw_document_id=None,
                source_url=source_url,
                acquired_at=None,
                extractor_version=EXTRACTOR_VERSION,
                provenance="semantic_normalization_v4 identity audit",
                linkage_status="UNKNOWN",
                no_linkage_reason=reason,
            )
            claims = ()
        else:
            lineage = EvidenceLineage(
                observation_id=observation_id,
                source_id=source,
                raw_document_id=document["id"],
                source_url=source_url,
                acquired_at=document["acquired_at"] or None,
                extractor_version=EXTRACTOR_VERSION,
                provenance=document["path"],
                raw_document_path=document["path"],
                raw_document_hash=document["hash"],
                linkage_status="TRACEABLE_RAW",
            )
            claims = extract_claims_from_explicit_basis(
                observation_id=observation_id,
                raw_basis=row["economic_object_raw"],
                raw_document_id=document["id"],
                provenance=document["path"],
            )
            claim_counts.update(claim.dimension for claim in claims)
            provenance_counts.update(claim.extraction_method.value for claim in claims)
        evidence_rows.append(OfferReachChargedScopeEvidence(observation_id, lineage, claims))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for evidence in evidence_rows:
            payload = {
                "schema_version": SCHEMA_VERSION,
                "version": version,
                "observation_id": evidence.observation_id,
                "lineage": _jsonable(evidence.lineage),
                "claims": [_jsonable(claim) for claim in evidence.claims],
            }
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")

    traceable = sum(item.lineage.linkage_status == "TRACEABLE_RAW" for item in evidence_rows)
    with_raw_document = sum(item.lineage.source_id in documents for item in evidence_rows)
    with_claims = sum(bool(item.claims) for item in evidence_rows)
    metrics: dict[str, Any] = {
        "TOTAL_OBSERVATIONS": len(evidence_rows),
        "WITH_RAW_DOCUMENT": with_raw_document,
        "WITH_SOURCE_URL": sum(bool(item.lineage.source_url) for item in evidence_rows),
        "WITH_TRACEABLE_RAW": traceable,
        "TRACEABLE_RAW": traceable,
        "WITHOUT_TRACEABLE_RAW": len(evidence_rows) - traceable,
        "RAW_DOCUMENTS_USED": len({item.lineage.raw_document_id for item in evidence_rows if item.lineage.raw_document_id}),
        "RAW_REPROCESS_COUNT": len(documents),
        "NETWORK_REACQUIRE_COUNT": 0,
        "BLOCKED_COUNT": 0,
        "EXTRACTED_REACH": claim_counts["geographic_reach"],
        "EXTRACTED_CHARGED_SCOPE": claim_counts["charged_unit"],
        "EXTRACTED_DELIVERY_MODE": claim_counts["delivery_mode"],
        "EXTRACTED_TRAVEL_RESTRICTIONS": claim_counts["travel_restriction"],
        "NO_REACH_EVIDENCE": len(evidence_rows) - sum(any(c.dimension == "geographic_reach" for c in item.claims) for item in evidence_rows),
        "NO_SCOPE_EVIDENCE": len(evidence_rows) - sum(any(c.dimension == "charged_unit" for c in item.claims) for item in evidence_rows),
        "CONFLICTING_CLAIMS": 0,
        "AMBIGUOUS_CLAIMS": 0,
        "LINEAGE_COVERAGE": round(traceable / len(evidence_rows), 6) if evidence_rows else 0,
        "RAW_LINKAGE_YIELD": round(traceable / with_raw_document, 6) if with_raw_document else 0,
        "EXTRACTION_YIELD": round(with_claims / traceable, 6) if traceable else 0,
        "NO_LINKAGE_REASONS": dict(sorted(reasons.items())),
        "CLAIMS_BY_DIMENSION": dict(sorted(claim_counts.items())),
        "CLAIMS_BY_PROVENANCE": dict(sorted(provenance_counts.items())),
    }
    output.with_suffix(".summary.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "version": version, "metrics": metrics}, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return metrics


def load_offer_evidence_sidecar(path: str | Path) -> dict[str, OfferReachChargedScopeEvidence]:
    result = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported offer evidence schema at line {line_number}.")
        observation_id = str(payload.get("observation_id") or "").strip()
        if not observation_id or observation_id in result:
            raise ValueError(f"Invalid or duplicate observation_id at line {line_number}.")
        lineage = EvidenceLineage(**payload["lineage"])
        claims = tuple(SourceEconomicClaim(
            observation_id=item["observation_id"],
            dimension=item["dimension"],
            value=item["value"],
            raw_basis=item["raw_basis"],
            raw_document_id=item["raw_document_id"],
            extraction_method=SourceClaimMethod(item["extraction_method"]),
            provenance=item["provenance"],
            status=SourceClaimStatus(item["status"]),
            version=item["version"],
            qualifiers=tuple(item.get("qualifiers", ())),
        ) for item in payload.get("claims", ()))
        result[observation_id] = OfferReachChargedScopeEvidence(observation_id, lineage, claims)
    return result


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value
