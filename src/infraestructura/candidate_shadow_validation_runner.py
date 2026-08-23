from __future__ import annotations

import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from src.dominio.candidate_shadow_validation import (
    CandidateShadowValidationCase,
    DatasetPartition,
    ExpectedCondition,
    validate_candidate_shadow,
)


RUNNER_VERSION = "candidate-shadow-validation-runner-v1"
DATASET_VERSION = "candidate-shadow-validation-dataset-v1"


def run_candidate_shadow_validation(
    root: str | Path,
    *,
    candidate_id: str,
    audit_path: str | Path,
    dataset_path: str | Path,
    results_path: str | Path,
    summary_path: str | Path,
    requests_path: str | Path,
) -> dict:
    root = Path(root)
    candidates = _jsonl(root / "data/knowledge_candidates_v1.jsonl")
    candidate = next((item for item in candidates if item["candidate_id"] == candidate_id), None)
    if candidate is None:
        raise ValueError(f"Unknown candidate_id: {candidate_id}")
    if candidate["validation_readiness"] != "READY_FOR_SHADOW_VALIDATION":
        raise ValueError("Runner accepts only READY_FOR_SHADOW_VALIDATION candidates.")
    plans = _jsonl(root / "data/candidate_shadow_validation_plans_v1.jsonl")
    plan = next((item for item in plans if item["candidate_id"] == candidate_id), None)
    if plan is None or plan.get("challenger_mode") != "SHADOW_ONLY":
        raise ValueError("Candidate requires a SHADOW_ONLY validation plan.")

    normalization = {row["observation_id"]: row for row in _csv(root / "data/semantic_normalization_v4.csv")}
    dimensions = {row["observation_id"]: row for row in _jsonl(root / "data/economic_dimensions_v2.jsonl")}
    offer_evidence = _jsonl(root / "data/offer_evidence_v1.jsonl")
    cases = _build_dataset(root, candidate, normalization, dimensions, offer_evidence)
    _write_jsonl(dataset_path, (_case_payload(item) for item in cases))

    conflicts_preserved = all(
        dimensions[str(observation_id)]["dimensions"]["currency"]["status"] == "CONFLICTED"
        for observation_id in (159, 160, 161)
    )
    result = validate_candidate_shadow(
        candidate_id=candidate_id,
        candidate_version=candidate["candidate_version"],
        candidate_scope=candidate["scope"],
        proposed_knowledge=candidate["proposed_knowledge"],
        cases=cases,
        dataset_version=DATASET_VERSION,
        runner_version=RUNNER_VERSION,
        champion_conflicts_preserved=conflicts_preserved,
        validation_dataset="candidate_shadow_validation_dataset_v1.jsonl",
    )
    result_payload = {"schema_version": "candidate-shadow-validation-result-v1", **_json_value(asdict(result))}
    _append_history(results_path, result_payload, result.validation_run_id)
    request_rows = []
    if result.evidence_request:
        request_rows.append({"schema_version": "candidate-shadow-validation-evidence-request-v1", **_json_value(asdict(result.evidence_request))})
    _write_jsonl(requests_path, request_rows)

    controls = sum(item.partition is DatasetPartition.HOLDOUT and not item.in_candidate_scope for item in cases)
    support_sources = {item.source_id for item in cases if item.partition is DatasetPartition.SUPPORT}
    support_providers = {item.provider_id for item in cases if item.partition is DatasetPartition.SUPPORT}
    control_cases = tuple(item for item in cases if item.partition is DatasetPartition.HOLDOUT and not item.in_candidate_scope)
    metrics = {
        "CANDIDATE_ID": candidate_id,
        "VALIDATION_RUN_ID": result.validation_run_id,
        "TOTAL_VALIDATION_CASES": result.total_validation_cases,
        "SUPPORT_CASES": result.support_cases,
        "HOLDOUT_CASES": result.holdout_cases,
        "UNIQUE_VALIDATION_PROVIDERS": result.independent_validation_provider_count,
        "UNIQUE_VALIDATION_SOURCES": result.independent_validation_source_count,
        "UNIQUE_VALIDATION_RAW_DOCUMENTS": result.independent_validation_raw_document_count,
        "TEMPORAL_VALIDATION_VERSIONS": result.temporal_versions_tested,
        "SAME_SOURCE_TEMPORAL_HOLDOUTS": sum(item.source_id in support_sources for item in control_cases),
        "CROSS_SOURCE_CONTROL_PROVIDERS": len({item.provider_id for item in control_cases if item.provider_id not in support_providers}),
        "CROSS_SOURCE_CONTROL_SOURCES": len({item.source_id for item in control_cases if item.source_id not in support_sources}),
        "CHAMPION_UNKNOWN": result.champion_unknown,
        "CHALLENGER_UNKNOWN": result.challenger_unknown,
        "CHALLENGER_SUPPORTED": result.challenger_supported,
        "FALSE_POSITIVES": result.false_positives,
        "FALSE_NEGATIVES": result.false_negatives,
        "UNKNOWN_SAFELY_PRESERVED": result.unknown_safely_preserved,
        "CONFLICTS_PRESERVED": result.conflicts_preserved,
        "PROVENANCE_PRESERVED": result.provenance_preserved,
        "SCOPE_VIOLATIONS": result.scope_violations,
        "TEMPORAL_VIOLATIONS": result.temporal_violations,
        "NEGATIVE_CONTROLS": controls,
        "VALIDATION_OUTCOME": result.outcome.value,
        "AUTO_PROMOTIONS": 0,
        "RUNTIME_WRITES": 0,
        "NETWORK_REQUESTS": 0,
    }
    _write_json(summary_path, {"schema_version": "candidate-shadow-validation-summary-v1", "metrics": metrics})
    _write_json(audit_path, {
        "schema_version": "candidate-shadow-validation-audit-v1",
        "candidate_id": candidate_id,
        "proposed_knowledge": candidate["proposed_knowledge"],
        "scope": candidate["scope"],
        "support_observations": candidate["evidence_summary"]["observation_count"],
        "support_providers": candidate["evidence_summary"]["provider_count"],
        "support_sources": candidate["evidence_summary"]["source_count"],
        "support_raw_documents": candidate["evidence_summary"]["raw_document_count"],
        "temporal_versions": candidate["evidence_summary"]["temporal_versions"],
        "contradictions": candidate["evidence_summary"]["contradiction_count"],
        "potential_reuse": candidate["potential_reuse"],
        "evidence_links": candidate["supporting_evidence"],
        "validation_plan": plan,
    })
    return metrics


def _build_dataset(root, candidate, normalization, dimensions, offer_evidence):
    support_sources = {item["source_id"] for item in candidate["supporting_evidence"]}
    cases = []
    for evidence in candidate["supporting_evidence"]:
        raw_path = root / evidence["raw_document_id"]
        row = normalization[evidence["observation_id"]]
        cases.append(CandidateShadowValidationCase(
            case_id=f"support:{evidence['evidence_id']}", candidate_id=candidate["candidate_id"],
            candidate_version=candidate["candidate_version"], observation_id=evidence["observation_id"],
            provider_id=evidence["provider_id"], source_id=evidence["source_id"],
            raw_document_id="sha256:" + _digest(raw_path), raw_document_path=evidence["raw_document_id"],
            raw_document_hash=_digest(raw_path), temporal_version=evidence["temporal_version"],
            extraction_version=evidence["temporal_version"], partition=DatasetPartition.SUPPORT,
            expected_condition=ExpectedCondition.NO_EXPLICIT_EVIDENCE,
            raw_basis=row["economic_object_raw"], provenance_reference=evidence["provenance_reference"],
            in_candidate_scope=True, replay_explicit_hardware=None,
        ))

    traceable = [
        item for item in offer_evidence
        if item["lineage"]["linkage_status"] == "TRACEABLE_RAW"
        and item["lineage"]["source_id"] not in support_sources
    ]
    selected = {}
    for item in sorted(traceable, key=lambda value: int(value["observation_id"])):
        observation_id = item["observation_id"]
        dimension = dimensions[observation_id]["dimensions"]["hardware_included"]
        condition = (
            ExpectedCondition.EXPLICIT_INCLUDED if dimension["status"] == "OBSERVED" and dimension["value"] is True
            else ExpectedCondition.EXPLICIT_EXCLUDED if dimension["status"] == "OBSERVED" and dimension["value"] is False
            else ExpectedCondition.UNKNOWN
        )
        selected.setdefault(condition, item)
    for condition in (ExpectedCondition.EXPLICIT_INCLUDED, ExpectedCondition.EXPLICIT_EXCLUDED, ExpectedCondition.UNKNOWN):
        item = selected.get(condition)
        if item is None:
            continue
        observation_id = item["observation_id"]
        lineage = item["lineage"]
        raw_path = root / lineage["raw_document_path"]
        dimension = dimensions[observation_id]["dimensions"]["hardware_included"]
        raw_basis = dimension["claims"][0]["raw_basis"] if dimension["claims"] else normalization[observation_id]["economic_object_raw"]
        provider = dimensions[observation_id]["dimensions"]["provider_identity"]["value"]["provider_id"]
        cases.append(CandidateShadowValidationCase(
            case_id=f"holdout-control:{observation_id}:{condition.value}",
            candidate_id=candidate["candidate_id"], candidate_version=candidate["candidate_version"],
            observation_id=observation_id, provider_id=provider, source_id=lineage["source_id"],
            raw_document_id=lineage["raw_document_id"], raw_document_path=lineage["raw_document_path"],
            raw_document_hash=_digest(raw_path), temporal_version=item["version"],
            extraction_version=lineage["extractor_version"], partition=DatasetPartition.HOLDOUT,
            expected_condition=condition, raw_basis=raw_basis,
            provenance_reference=lineage["provenance"], in_candidate_scope=False,
            replay_explicit_hardware=(True if condition is ExpectedCondition.EXPLICIT_INCLUDED else False if condition is ExpectedCondition.EXPLICIT_EXCLUDED else None),
        ))
    return tuple(sorted(cases, key=lambda item: item.case_id))


def _case_payload(item):
    return {"schema_version": DATASET_VERSION, **_json_value(asdict(item))}


def _append_history(path, payload, run_id):
    rows = _jsonl(path)
    existing = next((item for item in rows if item["validation_run_id"] == run_id), None)
    if existing is not None and existing != payload:
        raise ValueError("Validation run id collision with different content.")
    if existing is None:
        rows.append(payload)
    _write_jsonl(path, sorted(rows, key=lambda item: item["validation_run_id"]))


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _jsonl(path):
    source = Path(path)
    if not source.exists():
        return []
    return [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]


def _json_value(value):
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if hasattr(value, "value") and hasattr(value, "name"):
        return value.value
    return value


def _write_json(path, payload):
    output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(_json_value(payload), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    output = Path(path); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(_json_value(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
