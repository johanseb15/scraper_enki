from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import unicodedata

from src.dominio.knowledge_candidate import (
    CandidateEvidence,
    CandidateType,
    CandidateValidationReadiness,
    KnowledgeCandidate,
    build_candidate_evidence_request,
    build_shadow_validation_plan,
)


VERSION = "knowledge-candidate-v1"


def build_knowledge_candidate_artifacts(
    root: str | Path,
    *,
    audit: str | Path,
    candidates: str | Path,
    summary: str | Path,
    requests: str | Path,
    plans: str | Path,
    alignment: str | Path,
) -> dict:
    root = Path(root)
    normalization = _csv(root / "data/semantic_normalization_v4.csv")
    registry = {row["source"]: row for row in _csv(root / "data/pricing_sources.csv")}
    dimensions = {row["observation_id"]: row for row in _jsonl(root / "data/economic_dimensions_v2.jsonl")}
    gaps = _jsonl(root / "data/economic_evidence_gap_register_v1.jsonl")
    pairs = _jsonl(root / "data/economic_evidence_pairs_v1.jsonl")
    outcomes = _jsonl(root / "data/acquisition_outcomes_v1.jsonl")
    claims = _jsonl(root / "data/targeted_source_claims_v1.jsonl")

    row_by_id = {row["observation_id"]: row for row in normalization}
    provider_by_source = {
        source: _provider_id_for_source(source, dimensions, registry)
        for source in registry
    }
    generated = []
    generated.extend(_gap_candidates(gaps, row_by_id, provider_by_source))
    generated.extend(_pair_gap_candidates(pairs, row_by_id, provider_by_source))
    generated.extend(_acquisition_candidates(outcomes, row_by_id, provider_by_source))
    generated.extend(_claim_candidates(claims, row_by_id, provider_by_source))
    generated.extend(_currency_conflict_candidates(dimensions, row_by_id, provider_by_source))
    generated = tuple(sorted(generated, key=lambda item: item.candidate_id))

    audit_payload = _audit(normalization, dimensions, gaps, pairs, outcomes, claims, generated)
    _write_json(audit, audit_payload)
    _write_jsonl(candidates, (_candidate_payload(item) for item in generated))

    evidence_requests = tuple(
        build_candidate_evidence_request(item)
        for item in generated
        if item.validation_readiness is not CandidateValidationReadiness.READY_FOR_SHADOW_VALIDATION
    )
    ranked_requests = tuple(sorted(evidence_requests, key=lambda item: (-item.acquisition_priority, item.request_id)))
    _write_jsonl(
        requests,
        ({"schema_version": "candidate-evidence-request-v1", "rank": rank, **_json_value(asdict(item))}
         for rank, item in enumerate(ranked_requests, 1)),
    )

    ready = tuple(item for item in generated if item.validation_readiness is CandidateValidationReadiness.READY_FOR_SHADOW_VALIDATION)
    shadow_plans = tuple(
        build_shadow_validation_plan(
            item,
            affected_subsystem=item.potential_reuse[0],
            golden_datasets=_validation_datasets(item)[0],
            real_datasets=_validation_datasets(item)[1],
        )
        for item in ready
    )
    _write_jsonl(plans, ({"schema_version": "candidate-shadow-validation-plan-v1", **_json_value(asdict(item))} for item in shadow_plans))

    metrics = _metrics(generated, ranked_requests, shadow_plans)
    _write_json(summary, {"schema_version": "knowledge-candidates-v1-summary", "version": VERSION, "metrics": metrics})
    _write_json(alignment, {
        "schema_version": "rector-learning-alignment-v1",
        "ENTENDER": {"epistemic_states_explicit": True, "unknown_preserved": True, "provenance_required": True},
        "CONECTAR": {"candidate_evidence_links": True, "gap_and_pair_links": True},
        "APRENDER": {"candidates_generated": len(generated), "conflicts_preserved": True, "auto_promotion": False},
        "EXPLOTAR": {"new_public_economic_decision": False, "runtime_integration": False},
    })
    return metrics


def _validation_datasets(candidate):
    if candidate.candidate_type is CandidateType.ACQUISITION_PATTERN_CANDIDATE:
        return (), (
            "data/acquisition_outcomes_v1.jsonl",
            "data/targeted_acquisition_manifest_v1.jsonl",
            "data/economic_dimensions_v2.jsonl",
        )
    return (
        "data/language/golden_corpus_v1.jsonl",
        "data/language/real_query_corpus_v1.jsonl",
    ), (
        "data/semantic_normalization_v4.csv",
        "data/economic_dimensions_v2.jsonl",
    )


def _gap_candidates(gaps, rows, providers):
    grouped = {}
    for gap in gaps:
        for blocker in gap["blockers"]:
            if blocker == "CONFLICTED_CURRENCY":
                continue
            grouped.setdefault(blocker, []).append(gap)
    result = []
    for blocker, items in sorted(grouped.items()):
        support = tuple(_row_evidence(
            evidence_id=f"gap:{item['observation_id']}:{blocker}",
            kind="ECONOMIC_GAP",
            row=rows[item["observation_id"]],
            provider=providers.get(rows[item["observation_id"]]["source"]),
            provenance="data/economic_evidence_gap_register_v1.jsonl",
            origin="GAP_REGISTER_DERIVATION",
            value=blocker,
        ) for item in items)
        result.append(KnowledgeCandidate.create(
            candidate_type=CandidateType.GAP_PATTERN_CANDIDATE,
            proposed_knowledge=f"{blocker} is a recurrent explicit evidence gap",
            scope="economic_evidence:global",
            context={"blocker": blocker},
            supporting_evidence=support,
            potential_reuse=("acquisition", "economic_dimensions", "pricing_evidence"),
            first_seen="economic-evidence-gap-register-v1",
            last_seen="economic-evidence-gap-register-v1",
        ))
    return result


def _pair_gap_candidates(pairs, rows, providers):
    grouped = {}
    for pair in pairs:
        if pair["compatibility_state"] != "MISSING_EVIDENCE":
            continue
        for missing in pair["missing_evidence"]:
            grouped.setdefault(missing["dimension"], []).append((pair, missing))
    result = []
    for dimension, entries in sorted(grouped.items()):
        evidence_by_id = {}
        for pair, missing in entries:
            observation_id = missing["observation_id"]
            row = rows[observation_id]
            evidence = _row_evidence(
                evidence_id=f"pair-gap:{pair['pair_id']}:{observation_id}:{dimension}",
                kind="BILATERAL_PAIR_GAP",
                row=row,
                provider=providers.get(row["source"]),
                provenance="data/economic_evidence_pairs_v1.jsonl",
                origin="PAIR_SHADOW_ANALYSIS",
                value=dimension,
                pair_ids=(pair["pair_id"],),
            )
            evidence_by_id[evidence.evidence_id] = evidence
        result.append(KnowledgeCandidate.create(
            candidate_type=CandidateType.GAP_PATTERN_CANDIDATE,
            proposed_knowledge=f"bilateral comparability recurrently lacks {dimension}",
            scope="cohort:VISITA_TECNICA_DOMICILIO",
            context={"dimension": dimension, "relation": "bilateral"},
            supporting_evidence=tuple(evidence_by_id.values()),
            potential_reuse=("acquisition", "economic_dimensions", "pricing_evidence"),
            first_seen="economic-evidence-pair-v1",
            last_seen="economic-evidence-pair-v1",
        ))
    return result


def _acquisition_candidates(outcomes, rows, providers):
    grouped = {}
    for item in outcomes:
        grouped.setdefault((item["status"], item["requested_dimension"]), []).append(item)
    result = []
    for (status, dimension), items in sorted(grouped.items()):
        support = []
        for item in items:
            row = rows[item["observation_id"]]
            support.append(_row_evidence(
                evidence_id=item["action_id"], kind="ACQUISITION_OUTCOME", row=row,
                provider=providers.get(row["source"]), provenance=item["provenance"],
                origin="ACQUISITION_OUTCOME", value=status,
                raw_document_id=item.get("raw_document_reference"),
                outcome_id=item["action_id"],
            ))
        result.append(KnowledgeCandidate.create(
            candidate_type=CandidateType.ACQUISITION_PATTERN_CANDIDATE,
            proposed_knowledge=f"targeted acquisition for {dimension} recurrently yields {status}",
            scope="targeted_acquisition:v1",
            context={"dimension": dimension, "outcome": status},
            supporting_evidence=tuple(support),
            potential_reuse=("acquisition", "economic_dimensions"),
            first_seen="acquisition-outcome-v1", last_seen="acquisition-outcome-v1",
        ))
    return result


def _claim_candidates(claims, rows, providers):
    result = []
    for claim in claims:
        row = rows[claim["observation_id"]]
        support = _row_evidence(
            evidence_id=f"claim:{claim['observation_id']}:{claim['dimension']}:{claim['value']}",
            kind="SOURCE_CLAIM", row=row, provider=providers.get(row["source"]),
            provenance=claim["provenance"], origin="RAW_SOURCE_OBSERVATION", value=claim["value"],
            raw_document_id=claim["raw_document_id"], claim_id=f"{claim['observation_id']}:{claim['dimension']}",
        )
        result.append(KnowledgeCandidate.create(
            candidate_type=CandidateType.DIMENSION_EXTRACTION_CANDIDATE,
            proposed_knowledge=f"phrase '{claim['raw_basis']}' may indicate {claim['dimension']}={claim['value']}",
            scope=f"economic_dimension:{claim['dimension']}",
            context={"extraction_method": claim["extraction_method"]},
            supporting_evidence=(support,),
            potential_reuse=("economic_dimensions", "pricing_evidence"),
            first_seen=claim["version"], last_seen=claim["version"],
        ))
    return result


def _currency_conflict_candidates(dimensions, rows, providers):
    support, conflicts = [], []
    for observation_id, item in sorted(dimensions.items(), key=lambda pair: int(pair[0])):
        currency = item["dimensions"]["currency"]
        if currency["status"] != "CONFLICTED":
            continue
        row = rows[observation_id]
        for index, claim in enumerate(currency["claims"]):
            evidence = _row_evidence(
                evidence_id=f"currency:{observation_id}:{index}:{claim['value']}", kind="DIMENSION_CLAIM",
                row=row, provider=providers.get(row["source"]), provenance=claim["provenance"]["origin_reference"],
                origin=claim["origin"], value=claim["value"], claim_id=f"{observation_id}:currency:{index}",
            )
            (support if claim["value"] == "USD" else conflicts).append(evidence)
    if not support:
        return []
    return [KnowledgeCandidate.create(
        candidate_type=CandidateType.DIMENSION_EXTRACTION_CANDIDATE,
        proposed_knowledge="currency marker 'u$s' may indicate currency=USD",
        scope="economic_dimension:currency",
        context={"language": "es-AR", "marker": "u$s"},
        supporting_evidence=tuple(support), contradicting_evidence=tuple(conflicts),
        potential_reuse=("economic_dimensions", "pricing_evidence"),
        first_seen="economic-evidence-dimensions-v2", last_seen="economic-evidence-dimensions-v2",
    )]


def _row_evidence(*, evidence_id, kind, row, provider, provenance, origin, value, pair_ids=(), raw_document_id=None, claim_id=None, outcome_id=None):
    return CandidateEvidence(
        evidence_id=evidence_id, evidence_kind=kind, observation_id=row["observation_id"],
        provider_id=provider, source_id=row["source"], raw_document_id=raw_document_id,
        claim_id=claim_id, acquisition_outcome_id=outcome_id, pair_ids=pair_ids,
        provenance_reference=provenance, origin_type=origin,
        temporal_version=row.get("extractor_version") or VERSION, value=value,
    )


def _audit(normalization, dimensions, gaps, pairs, outcomes, claims, candidates):
    semantic = {}
    for row in normalization:
        key = (_fold(row["economic_object_raw"]), row["canonical_service"])
        semantic.setdefault(key, []).append(row)
    dimension_patterns = set()
    conflicts = 0
    for item in dimensions.values():
        for name, dimension in item["dimensions"].items():
            if dimension["status"] in {"CONFLICTED", "AMBIGUOUS"}:
                conflicts += 1
            for claim in dimension["claims"]:
                dimension_patterns.add((name, json.dumps(claim["value"], ensure_ascii=False, sort_keys=True), claim["origin"]))
    by_source_type = {
        "SEMANTIC_MAPPING": len(semantic),
        "ECONOMIC_DIMENSION": len(dimension_patterns),
        "GAP_REGISTER": len({blocker for row in gaps for blocker in row["blockers"]}),
        "PAIR_ANALYSIS": len({item["dimension"] for pair in pairs for item in pair["missing_evidence"]}),
        "ACQUISITION_OUTCOME": len({(item["status"], item["requested_dimension"]) for item in outcomes}),
        "TARGETED_SOURCE_CLAIM": len({(item["dimension"], item["value"]) for item in claims}),
    }
    runtime_used = sum(any(row["semantic_role"] == "SINGLE_SERVICE" and row["canonical_service"] for row in rows) for rows in semantic.values())
    total = sum(by_source_type.values())
    provider_histogram = {}
    source_histogram = {}
    for candidate in candidates:
        provider_histogram[str(candidate.evidence_summary.provider_count)] = provider_histogram.get(str(candidate.evidence_summary.provider_count), 0) + 1
        source_histogram[str(candidate.evidence_summary.source_count)] = source_histogram.get(str(candidate.evidence_summary.source_count), 0) + 1
    return {
        "schema_version": "knowledge-observation-audit-v1", "version": VERSION,
        "metrics": {
            "TOTAL_POTENTIAL_PATTERNS": total, "BY_SOURCE_TYPE": dict(sorted(by_source_type.items())),
            "BY_DOMAIN": {"SEMANTIC": len(semantic), "ECONOMIC": total - len(semantic)},
            "BY_PROVIDER_COUNT": dict(sorted(provider_histogram.items())),
            "BY_SOURCE_COUNT": dict(sorted(source_histogram.items())),
            "WITH_CONTRADICTION": conflicts, "WITHOUT_CONTRADICTION": total - conflicts,
            "CURRENTLY_RUNTIME_USED": runtime_used, "SHADOW_ONLY": total - runtime_used,
            "HISTORICAL_ONLY": 0,
        },
    }


def _metrics(candidates, requests, plans):
    by_type = {}
    reuse = {}
    for item in candidates:
        by_type[item.candidate_type.value] = by_type.get(item.candidate_type.value, 0) + 1
        for target in item.potential_reuse:
            reuse[target] = reuse.get(target, 0) + 1
    return {
        "TOTAL_CANDIDATES": len(candidates), "CANDIDATES_BY_TYPE": dict(sorted(by_type.items())),
        "SUPPORTED": sum(item.epistemic_status.value == "SUPPORTED" for item in candidates),
        "CONFLICTED": sum(item.epistemic_status.value == "CONFLICTED" for item in candidates),
        "INSUFFICIENT": sum(item.epistemic_status.value == "INSUFFICIENT" for item in candidates),
        "QUARANTINED": sum(item.epistemic_status.value == "QUARANTINED" for item in candidates),
        "READY_FOR_SHADOW_VALIDATION": sum(item.validation_readiness.value == "READY_FOR_SHADOW_VALIDATION" for item in candidates),
        "TOTAL_SUPPORTING_OBSERVATIONS": sum(item.evidence_summary.observation_count for item in candidates),
        "UNIQUE_SUPPORTING_PROVIDERS": len({e.provider_id for item in candidates for e in item.supporting_evidence if e.provider_id}),
        "UNIQUE_SUPPORTING_SOURCES": len({e.source_id for item in candidates for e in item.supporting_evidence if e.source_id}),
        "RAW_EVIDENCE_SUPPORT": sum(item.evidence_summary.raw_evidence_count for item in candidates),
        "NORMALIZED_EVIDENCE_SUPPORT": sum(item.evidence_summary.normalized_evidence_count for item in candidates),
        "CONTRADICTIONS": sum(item.evidence_summary.contradiction_count for item in candidates),
        "CANDIDATE_EVIDENCE_REQUESTS": len(requests), "SHADOW_VALIDATION_PLANS": len(plans),
        "KNOWLEDGE_REUSE_TARGET_COUNT": sum(len(item.potential_reuse) for item in candidates),
        "POTENTIAL_REUSE": dict(sorted(reuse.items())),
        "AUTO_PROMOTIONS": 0, "RUNTIME_WRITES": 0,
    }


def _candidate_payload(item):
    payload = _json_value(asdict(item))
    payload["schema_version"] = VERSION
    return payload


def _provider_id_for_source(source, dimensions, registry):
    for item in dimensions.values():
        value = item["dimensions"]["provider_identity"].get("value")
        if value and value.get("source") == source:
            return value["provider_id"]
    provider = registry.get(source, {}).get("provider")
    return f"provider:unresolved:{provider}" if provider else None


def _fold(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join("".join(char for char in normalized if not unicodedata.combining(char)).casefold().split())


def _csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _jsonl(path):
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _json_value(value):
    if is_dataclass(value):
        return _json_value(asdict(value))
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
