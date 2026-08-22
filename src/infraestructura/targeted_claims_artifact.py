from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from src.dominio.offer_evidence import SourceClaimMethod, SourceEconomicClaim
from src.infraestructura.offer_evidence_extractor import extract_claims_from_explicit_basis
from src.infraestructura.scrapers.generic_price_extractor import extraer_observaciones_precio_genericas


TARGET_IDS = ("62", "68", "69", "70", "234")
REQUESTED = {"geographic_reach", "hardware_included"}


def build_targeted_claims(
    normalization_path: str | Path,
    registry_path: str | Path,
    plan_path: str | Path,
    acquisition_manifest_path: str | Path,
    claims_path: str | Path,
    identities_path: str | Path,
    outcomes_path: str | Path,
    rejected_claims_path: str | Path,
) -> dict[str, Any]:
    rows = _csv(normalization_path, "observation_id")
    registry = _csv(registry_path, "source")
    plan = [json.loads(line) for line in Path(plan_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    acquisitions = {item["source"]: item for item in _jsonl(acquisition_manifest_path)}
    claims_rows = []
    identities = []
    outcomes = []
    rejected = []
    for observation_id in TARGET_IDS:
        row = rows[observation_id]
        source = row["source"]
        acquired = acquisitions.get(source)
        matching_actions = [item for item in plan if item["observation_id"] == observation_id]
        if not acquired or acquired["status"] != "SUCCEEDED":
            reason = acquired.get("reason", "SOURCE_NOT_ACQUIRED") if acquired else "SOURCE_NOT_ACQUIRED"
            identities.append(_identity(row, acquired, "UNRESOLVED", reason))
            for action in matching_actions:
                outcomes.append(_outcome(action, acquired, "ACQUISITION_FAILED", (), reason))
            continue
        raw_path = Path(acquired["raw_document_reference"])
        content = raw_path.read_bytes()
        encoding = "utf-8"
        try:
            html = content.decode(encoding)
        except UnicodeDecodeError:
            html = content.decode("latin-1")
        observed = extraer_observaciones_precio_genericas(
            html,
            source=source,
            provider=registry[source]["provider"],
            source_url=acquired["source_url"],
            raw_document_id=1,
            retrieved_at=datetime.fromisoformat(acquired["acquired_at"]),
            content_hash=acquired["content_hash"],
        )
        match = next((item for item in observed if _same_offer(row, item)), None)
        if match is None:
            identities.append(_identity(row, acquired, "UNRESOLVED", "TEMPORAL_MISMATCH_OR_OFFER_NOT_FOUND"))
            for action in matching_actions:
                outcomes.append(_outcome(action, acquired, "TEMPORAL_MISMATCH", (), "Current page does not reproduce historical offer identity and price."))
            continue
        offer_key = f"{match.source_record_id}|{match.price_value}|{match.currency_raw}"
        identities.append({
            **_identity(row, acquired, "RESOLVED", "Exact source/object/price/currency match."),
            "offer_key": offer_key,
            "extraction_path": f"generic_price_extractor_v3/{match.source_record_id}",
        })
        extracted = extract_claims_from_explicit_basis(
            observation_id=observation_id,
            raw_basis=str(match.economic_object_raw),
            raw_document_id=f"sha256:{acquired['content_hash']}",
            provenance=acquired["raw_document_reference"],
            method=SourceClaimMethod.DERIVED_FROM_SOURCE_TEXT,
        )
        useful = [claim for claim in extracted if claim.dimension in REQUESTED]
        useful.extend(_structured_offer_claims(row, html, acquired))
        if _page_has_unattributed_hardware_context(html, str(match.economic_object_raw)):
            rejected.append({
                "schema_version": "rejected-targeted-source-claim-v1",
                "observation_id": observation_id,
                "dimension": "hardware_included",
                "reason": "AMBIGUOUS_APPLICABILITY",
                "raw_basis": "Page-level hardware/repuestos context outside exact priced offer block.",
                "raw_document_id": f"sha256:{acquired['content_hash']}",
                "source_url": acquired["source_url"],
                "acquired_at": acquired["acquired_at"],
            })
        for claim in useful:
            claims_rows.append({
                "schema_version": "versioned-targeted-source-claim-v1",
                "observation_id": observation_id,
                "dimension": claim.dimension,
                "value": claim.value,
                "raw_basis": claim.raw_basis,
                "raw_document_id": claim.raw_document_id,
                "source_url": acquired["source_url"],
                "acquired_at": acquired["acquired_at"],
                "extraction_path": f"generic_price_extractor_v3/{match.source_record_id}",
                "extraction_method": claim.extraction_method.value,
                "provenance": claim.provenance,
                "version": "versioned-targeted-source-claim-v1",
                "temporal_status": "COMPATIBLE_EXACT_OFFER_IDENTITY",
            })
        for action in matching_actions:
            found = tuple(item["dimension"] for item in claims_rows if item["observation_id"] == observation_id and item["dimension"] == action["target_dimension"])
            outcomes.append(_outcome(action, acquired, "EVIDENCE_FOUND" if found else "NO_EXPLICIT_EVIDENCE", found, "Exact offer identity resolved; requested explicit evidence absent." if not found else "Offer-attributable evidence extracted."))
    _write(claims_path, claims_rows)
    _write(identities_path, identities)
    _write(outcomes_path, outcomes)
    _write(rejected_claims_path, rejected)
    return {
        "TARGETS": len(TARGET_IDS),
        "OFFER_IDENTITIES_RESOLVED": sum(item["status"] == "RESOLVED" for item in identities),
        "OFFER_IDENTITIES_UNRESOLVED": sum(item["status"] != "RESOLVED" for item in identities),
        "CLAIMS_EXTRACTED": len(claims_rows),
        "AMBIGUOUS_APPLICABILITY_REJECTED": len(rejected) + sum(item["reason"] == "TEMPORAL_MISMATCH_OR_OFFER_NOT_FOUND" for item in identities),
        "TEMPORAL_MISMATCHES": sum(item["status"] == "TEMPORAL_MISMATCH" for item in outcomes),
    }


def _structured_offer_claims(row, html, acquired):
    if row["canonical_service"] != "VISITA_TECNICA_DOMICILIO":
        return []
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for element in soup.find_all(["meta", "a", "h1", "h2", "h3", "p"]):
        basis = element.get("content", "") if element.name == "meta" else element.get_text(" ", strip=True)
        if "servicio técnico" in basis.casefold() and "a domicilio en córdoba" in basis.casefold():
            candidates.append(basis.strip())
    if not candidates:
        return []
    basis = sorted(set(candidates), key=lambda value: (len(value), value))[0]
    return [SourceEconomicClaim(
        observation_id=row["observation_id"], dimension="geographic_reach", value="NAMED_AREA:Córdoba",
        raw_basis=basis, raw_document_id=f"sha256:{acquired['content_hash']}",
        extraction_method=SourceClaimMethod.STRUCTURED_SOURCE_FIELD,
        provenance=acquired["raw_document_reference"], version="versioned-targeted-source-claim-v1",
    )]


def _page_has_unattributed_hardware_context(html, local_basis):
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True).casefold()
    local = local_basis.casefold()
    return any(word in text for word in ("repuestos", "no incluye repuesto", "incluye repuesto")) and "repuesto" not in local


def load_targeted_source_claims(path: str | Path) -> dict[str, tuple[SourceEconomicClaim, ...]]:
    grouped = {}
    for item in _jsonl(path):
        if item.get("temporal_status") != "COMPATIBLE_EXACT_OFFER_IDENTITY":
            continue
        grouped.setdefault(item["observation_id"], []).append(SourceEconomicClaim(
            observation_id=item["observation_id"], dimension=item["dimension"], value=item["value"],
            raw_basis=item["raw_basis"], raw_document_id=item["raw_document_id"],
            extraction_method=SourceClaimMethod(item["extraction_method"]), provenance=item["provenance"],
            version=item["version"],
        ))
    return {key: tuple(value) for key, value in grouped.items()}


def _same_offer(row, observed):
    return (
        str(observed.economic_object_raw).strip() == row["economic_object_raw"].strip()
        and str(int(observed.price_value)) == str(int(float(row["price_value"])))
        and str(observed.currency_raw).strip() == row["currency"].strip()
    )


def _identity(row, acquired, status, reason):
    return {
        "schema_version": "offer-evidence-identity-v1", "observation_id": row["observation_id"],
        "source": row["source"], "raw_document_id": f"sha256:{acquired['content_hash']}" if acquired and acquired.get("content_hash") else None,
        "offer_key": None, "extraction_path": None, "status": status, "reason": reason,
    }


def _outcome(action, acquired, status, found, reason):
    return {
        "schema_version": "acquisition-outcome-v1", "action_id": action["action_id"], "observation_id": action["observation_id"],
        "source": action["source"], "requested_dimension": action["target_dimension"], "expected_unlock": action["unlock_potential"],
        "status": status, "evidence_found": list(found), "actual_unlock": 0, "new_conflicts": [],
        "unlock_delta": -action["unlock_potential"],
        "remaining_gaps": action["current_blockers"], "raw_document_reference": acquired.get("raw_document_reference") if acquired else None,
        "provenance": acquired.get("metadata_reference", "acquisition-manifest-v1") if acquired else "acquisition-manifest-v1", "reason": reason,
    }


def _csv(path, key):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def _jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _write(path, rows):
    output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows: handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
