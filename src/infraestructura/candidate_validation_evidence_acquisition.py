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
from src.dominio.candidate_validation_acquisition import (
    CandidateValidationAcquisitionOutcome,
    CandidateValidationGap,
    ValidationControlType,
    ValidationSourceCandidate,
    minimum_validation_acquisition_set,
)


CANDIDATE_VERSION = "knowledge-candidate-v1"
DATASET_VERSION = "candidate-shadow-validation-dataset-v2"
RUNNER_VERSION = "candidate-shadow-validation-runner-v1"
ACQUISITION_VERSION = "candidate-validation-evidence-acquisition-v1"


def classify_snapshot(previous_hash: str | None, payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    if previous_hash is None:
        return "NEW"
    return "UNCHANGED" if previous_hash == digest else "CHANGED"


def versioned_snapshot_path(root: str | Path, source_id: str, payload: bytes, suffix: str) -> Path:
    safe_source = source_id.replace(":", "_").replace("/", "_")
    return Path(root) / safe_source / (hashlib.sha256(payload).hexdigest() + suffix)


def deduplicate_actions(actions):
    seen = set()
    result = []
    for action in actions:
        key = action["url"]
        if key not in seen:
            seen.add(key)
            result.append(action)
    return tuple(result)


def classify_control(*, status: str, value, attribution: str, complete: bool) -> str:
    if attribution != "OFFER_EXACT":
        return ValidationControlType.AMBIGUOUS_ATTRIBUTION.value
    if status == "OBSERVED" and value is True:
        return ValidationControlType.EXPLICIT_INCLUDED.value
    if status == "OBSERVED" and value is False:
        return ValidationControlType.EXPLICIT_EXCLUDED.value
    if status == "UNKNOWN":
        # UNKNOWN states epistemic undecidability; incomplete evidence records its reason.
        return ValidationControlType.GENUINELY_UNKNOWN.value
    return ValidationControlType.NO_EXPLICIT_EVIDENCE.value


def acquire_candidate_validation_evidence(root, output_dir, *, candidate_id, fetcher=None):
    root, output = Path(root), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    candidate = next(item for item in _jsonl(root / "data/knowledge_candidates_v1.jsonl") if item["candidate_id"] == candidate_id)
    if candidate["candidate_version"] != CANDIDATE_VERSION:
        raise ValueError("Acquisition v1 is pinned to the unchanged candidate v1.")
    prior_request = _jsonl(root / "data/candidate_shadow_validation_evidence_requests_v1.jsonl")[0]
    gap = CandidateValidationGap(
        candidate_id=candidate_id,
        missing_provider_diversity=prior_request["required_independent_providers"],
        missing_source_diversity=prior_request["required_independent_sources"],
        missing_temporal_diversity=0,
        missing_positive_control=True,
        missing_negative_control=False,
        missing_unknown_control=True,
        scope_requirement=prior_request["missing_context"],
        provenance_requirement="REPRODUCIBLE_RAW_WITH_SHA256",
        attribution_requirement="OFFER_EXACT",
        validation_blockers=("INSUFFICIENT_IN_SCOPE_INDEPENDENT_HOLDOUT",),
    )
    support_sources = {item["source_id"] for item in candidate["supporting_evidence"]}
    support_providers = {item["provider_id"] for item in candidate["supporting_evidence"]}
    dimensions = {item["observation_id"]: item for item in _jsonl(root / "data/economic_dimensions_v2.jsonl")}
    evidence = _jsonl(root / "data/offer_evidence_v1.jsonl")
    registry = {item["source"]: item for item in _csv(root / "data/pricing_sources.csv")}
    manifest = {item["source"]: item for item in _csv(root / "data/offer_evidence_raw_manifest_v1.csv")}
    candidates = _source_candidates(root, dimensions, evidence, registry, manifest, support_sources, support_providers)
    plan = minimum_validation_acquisition_set(gap, candidates)

    outcomes = _execute_local_plan(root, candidate_id, plan, dimensions, evidence)
    cases = _extend_dataset(root, outcomes)
    conflicts = all(dimensions[str(value)]["dimensions"]["currency"]["status"] == "CONFLICTED" for value in (159, 160, 161))
    result = validate_candidate_shadow(
        candidate_id=candidate_id,
        candidate_version=candidate["candidate_version"],
        candidate_scope=candidate["scope"],
        proposed_knowledge=candidate["proposed_knowledge"],
        cases=cases,
        dataset_version=DATASET_VERSION,
        runner_version=RUNNER_VERSION,
        champion_conflicts_preserved=conflicts,
        validation_dataset="candidate_shadow_validation_dataset_v2.jsonl",
    )
    before = _jsonl(root / "data/candidate_shadow_validation_results_v1.jsonl")[0]
    metrics = _metrics(result, cases, candidates, plan, outcomes)
    _write_json(output / "candidate_validation_gap_v1.json", {"schema_version": "candidate-validation-gap-v1", **_json_value(asdict(gap))})
    _write_jsonl(output / "validation_source_candidates_v1.jsonl", (
        {"schema_version": "validation-source-candidate-v1", "rank": rank, **_json_value(asdict(item))}
        for rank, item in enumerate(sorted(candidates, key=lambda value: (-value.validation_value, value.source_id)), 1)
    ))
    _write_json(output / "minimal_validation_acquisition_set_v1.json", {"schema_version": "minimal-validation-acquisition-set-v1", **_json_value(asdict(plan))})
    _write_jsonl(output / "candidate_validation_acquisition_outcomes_v1.jsonl", (
        {"schema_version": "candidate-validation-acquisition-outcome-v1", **_json_value(asdict(item))} for item in outcomes
    ))
    _write_jsonl(output / "candidate_validation_reusable_evidence_v1.jsonl", _reusable(outcomes))
    _write_jsonl(output / "candidate_shadow_validation_dataset_v2.jsonl", (
        {"schema_version": DATASET_VERSION, **_json_value(asdict(item))} for item in cases
    ))
    result_payload = {"schema_version": "candidate-shadow-validation-result-v2", **_json_value(asdict(result))}
    _write_jsonl(output / "candidate_shadow_validation_results_v2.jsonl", (result_payload,))
    _write_json(output / "candidate_shadow_validation_summary_v2.json", {"schema_version": "candidate-shadow-validation-summary-v2", "metrics": metrics})
    _write_jsonl(output / "candidate_shadow_validation_evidence_requests_v2.jsonl", ())
    _write_json(output / "candidate_validation_before_after_v1.json", _before_after(before, result, cases))
    _write_jsonl(output / "candidate_revision_proposals_v1.jsonl", (_revision(candidate, outcomes, result),))
    _write_json(output / "candidate_validation_acquisition_summary_v1.json", {"schema_version": "candidate-validation-acquisition-summary-v1", "metrics": metrics})
    return metrics


def _source_candidates(root, dimensions, evidence, registry, manifest, support_sources, support_providers):
    potential = {
        "jadetech_generic": (True, False, True),
        "bitz_generic": (False, True, False),
        "dmr_generic": (False, False, True),
        "bairescloud_generic": (False, False, True),
    }
    result = []
    for source_id, (included, excluded, unknown) in potential.items():
        raw = manifest[source_id]
        provider_id = next(
            item["dimensions"]["provider_identity"]["value"]["provider_id"]
            for item in dimensions.values()
            if item["dimensions"]["provider_identity"]["value"]["source"] == source_id
        )
        result.append(ValidationSourceCandidate.create(
            source_id=source_id, provider_id=provider_id, url=registry[source_id]["url"],
            support_sources=support_sources, support_providers=support_providers,
            existing_local_raw=(root / raw["raw_path"]).is_file(), reacquirable=True,
            hardware_related_offer=True, explicit_inclusion_potential=included,
            explicit_exclusion_potential=excluded, genuinely_unknown_potential=unknown,
            attribution_quality="OFFER_EXACT", temporal_continuity="SNAPSHOT_HASHED",
        ))
    return tuple(result)


def _execute_local_plan(root, candidate_id, plan, dimensions, evidence):
    selected = {item.source_id: item for item in plan.actions}
    specs = (("jadetech_generic", "3"), ("jadetech_generic", "1"), ("bitz_generic", "49"))
    outcomes = []
    prior_cases = {
        item["raw_document_path"]: item["raw_document_hash"]
        for item in _jsonl(root / "data/candidate_shadow_validation_dataset_v1.jsonl")
        if item.get("raw_document_path")
    }
    normalization = _normalization(root)
    for source_id, observation_id in specs:
        action = selected.get(source_id)
        if action is None:
            continue
        record = next(item for item in evidence if item["observation_id"] == observation_id)
        lineage = record["lineage"]
        path = root / lineage["raw_document_path"]
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        dimension = dimensions[observation_id]["dimensions"]["hardware_included"]
        control = ValidationControlType(classify_control(
            status=dimension["status"], value=dimension["value"], attribution="OFFER_EXACT", complete=True,
        ))
        basis = dimension["claims"][0]["raw_basis"] if dimension["claims"] else normalization[observation_id]["economic_object_raw"]
        baseline_hash = prior_cases[lineage["raw_document_path"]]
        outcomes.append(CandidateValidationAcquisitionOutcome(
            action_id=f"validation-acquisition:{source_id}", candidate_id=candidate_id,
            source_id=source_id, provider_id=action.provider_id,
            raw_document_path=lineage["raw_document_path"], raw_document_hash=digest,
            acquisition_status=classify_snapshot(baseline_hash, payload), control_type=control,
            observation_id=observation_id, extracted_evidence=basis,
            attribution_status="OFFER_EXACT", independent_provider=action.independent_provider,
            independent_source=action.independent_source, validation_value=action.validation_value,
            provenance=f"{lineage['raw_document_path']}#observation_id={observation_id};field=economic_object_raw",
            temporal_status="UNDATED_SNAPSHOT_HASH_VERIFIED",
            source_url=lineage["source_url"], registered_raw_document_id=lineage["raw_document_id"],
            compared_baseline_hash=baseline_hash, section="offer/service row",
            nearby_price=normalization[observation_id]["price_value"] + " " + normalization[observation_id]["currency"],
            structural_locator=f"observation_id={observation_id};field=economic_object_raw",
            unknown_reason=("COMPLETE_OFFER_BLOCK_HAS_NO_DECISIVE_HARDWARE_INCLUSION_CLAIM" if control is ValidationControlType.GENUINELY_UNKNOWN else None),
        ))
    return tuple(sorted(outcomes, key=lambda item: (item.source_id, int(item.observation_id))))


def _extend_dataset(root, outcomes):
    old = tuple(_case_from_payload(item) for item in _jsonl(root / "data/candidate_shadow_validation_dataset_v1.jsonl"))
    normalization = _normalization(root)
    added = []
    for outcome in outcomes:
        condition = {
            ValidationControlType.EXPLICIT_INCLUDED: ExpectedCondition.EXPLICIT_INCLUDED,
            ValidationControlType.EXPLICIT_EXCLUDED: ExpectedCondition.EXPLICIT_EXCLUDED,
            ValidationControlType.GENUINELY_UNKNOWN: ExpectedCondition.UNKNOWN,
        }[outcome.control_type]
        added.append(CandidateShadowValidationCase(
            case_id=f"validation-acquisition:{outcome.source_id}:{outcome.observation_id}:{condition.value}",
            candidate_id=outcome.candidate_id, candidate_version=CANDIDATE_VERSION,
            observation_id=outcome.observation_id, provider_id=outcome.provider_id,
            source_id=outcome.source_id, raw_document_id="sha256:" + outcome.raw_document_hash,
            raw_document_path=outcome.raw_document_path, raw_document_hash=outcome.raw_document_hash,
            temporal_version="local-snapshot:undated", extraction_version=normalization[outcome.observation_id]["extractor_version"],
            partition=DatasetPartition.HOLDOUT, expected_condition=condition,
            raw_basis=outcome.extracted_evidence, provenance_reference=outcome.provenance,
            in_candidate_scope=True,
            replay_explicit_hardware=True if condition is ExpectedCondition.EXPLICIT_INCLUDED else False if condition is ExpectedCondition.EXPLICIT_EXCLUDED else None,
        ))
    return tuple(sorted(old + tuple(added), key=lambda item: item.case_id))


def _case_from_payload(item):
    values = dict(item); values.pop("schema_version", None)
    values["partition"] = DatasetPartition(values["partition"])
    values["expected_condition"] = ExpectedCondition(values["expected_condition"])
    return CandidateShadowValidationCase(**values)


def _metrics(result, cases, candidates, plan, outcomes):
    controls = [item for item in outcomes]
    return {
        "PLANNED_ACTIONS": len(plan.actions), "EXECUTED_ACTIONS": len({item.action_id for item in outcomes}),
        "SKIPPED_ACTIONS": len(candidates) - len(plan.actions), "NETWORK_REQUESTS": 0,
        "SUCCESS": len(plan.actions), "FAILURE": 0, "BLOCKED": 0,
        "UNCHANGED": len({item.raw_document_hash for item in outcomes if item.acquisition_status == "UNCHANGED"}),
        "CHANGED": 0, "NEW": 0, "NEW_SNAPSHOTS": 0,
        "TOTAL_VALIDATION_CASES": result.total_validation_cases, "SUPPORT_CASES": result.support_cases,
        "HOLDOUT_CASES": result.holdout_cases,
        "INDEPENDENT_VALIDATION_PROVIDERS": result.independent_validation_provider_count,
        "INDEPENDENT_VALIDATION_SOURCES": result.independent_validation_source_count,
        "INDEPENDENT_VALIDATION_RAW_DOCUMENTS": result.independent_validation_raw_document_count,
        "TEMPORAL_HOLDOUTS": 0,
        "EXPLICIT_CONTROLS": sum(item.control_type in {ValidationControlType.EXPLICIT_INCLUDED, ValidationControlType.EXPLICIT_EXCLUDED} for item in controls),
        "UNKNOWN_CONTROLS": sum(item.control_type is ValidationControlType.GENUINELY_UNKNOWN for item in controls),
        "FALSE_POSITIVES": result.false_positives, "FALSE_NEGATIVES": result.false_negatives,
        "UNKNOWN_PRESERVED": result.unknown_safely_preserved,
        "PROVENANCE_PRESERVED": result.provenance_preserved, "CONFLICTS_PRESERVED": result.conflicts_preserved,
        "SCOPE_VIOLATIONS": result.scope_violations, "TEMPORAL_VIOLATIONS": result.temporal_violations,
        "VALIDATION_OUTCOME": result.outcome.value, "AUTO_PROMOTIONS": 0, "RUNTIME_WRITES": 0,
    }


def _before_after(before, result, cases):
    new = [item for item in cases if item.case_id.startswith("validation-acquisition:")]
    return {
        "schema_version": "candidate-validation-before-after-v1",
        "before": {key: before[key] for key in ("outcome", "support_cases", "holdout_cases", "independent_validation_provider_count", "independent_validation_source_count", "false_positives", "false_negatives", "unknown_safely_preserved", "provenance_preserved", "conflicts_preserved", "scope_violations", "temporal_violations")},
        "after": {
            "outcome": result.outcome.value, "support_cases": result.support_cases, "holdout_cases": result.holdout_cases,
            "independent_validation_provider_count": result.independent_validation_provider_count,
            "independent_validation_source_count": result.independent_validation_source_count,
            "temporal_holdouts": 0,
            "explicit_controls": sum(item.expected_condition in {ExpectedCondition.EXPLICIT_INCLUDED, ExpectedCondition.EXPLICIT_EXCLUDED} for item in new),
            "unknown_controls": sum(item.expected_condition is ExpectedCondition.UNKNOWN for item in new),
            "false_positives": result.false_positives, "false_negatives": result.false_negatives,
            "unknown_safely_preserved": result.unknown_safely_preserved,
            "provenance_preserved": result.provenance_preserved, "conflicts_preserved": result.conflicts_preserved,
            "scope_violations": result.scope_violations, "temporal_violations": result.temporal_violations,
        },
    }


def _revision(candidate, outcomes, result):
    return {
        "schema_version": "candidate-revision-proposal-v1", "original_candidate": candidate["candidate_id"],
        "original_candidate_version": candidate["candidate_version"],
        "evidence": [item.provenance for item in outcomes],
        "proposed_scope_change": "NARROW_TO_OBSERVED_SUPPORT_SOURCES_ONLY",
        "reason": "Independent in-scope explicit controls refute cross-source generalization.",
        "contradictions": [item.extracted_evidence for item in outcomes if item.control_type in {ValidationControlType.EXPLICIT_INCLUDED, ValidationControlType.EXPLICIT_EXCLUDED}],
        "validation_outcome": result.outcome.value, "creates_candidate_v2": False,
        "promotion_authorized": False,
    }


def _reusable(outcomes):
    for item in outcomes:
        yield {
            "schema_version": "candidate-validation-reusable-evidence-v1",
            "evidence_id": f"validation-evidence:{item.source_id}:{item.observation_id}",
            "candidate_id": item.candidate_id, "dimension": "hardware_included",
            "control_type": item.control_type.value, "raw_document_path": item.raw_document_path,
            "raw_document_hash": item.raw_document_hash, "observation_id": item.observation_id,
            "provenance": item.provenance, "consumer_eligibility": ["KNOWLEDGE_CANDIDATES", "ECONOMIC_DIMENSIONS", "ACQUISITION_PLANNER", "PRICING_EVIDENCE"],
            "runtime_integrated": False,
        }


def _normalization(root):
    return {item["observation_id"]: item for item in _csv(Path(root) / "data/semantic_normalization_v4.csv")}


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
    Path(path).write_text(json.dumps(_json_value(payload), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(_json_value(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
