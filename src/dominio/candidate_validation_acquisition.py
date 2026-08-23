from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations


class ValidationControlType(Enum):
    EXPLICIT_INCLUDED = "EXPLICIT_INCLUDED"
    EXPLICIT_EXCLUDED = "EXPLICIT_EXCLUDED"
    GENUINELY_UNKNOWN = "GENUINELY_UNKNOWN"
    AMBIGUOUS_ATTRIBUTION = "AMBIGUOUS_ATTRIBUTION"
    NO_EXPLICIT_EVIDENCE = "NO_EXPLICIT_EVIDENCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


@dataclass(frozen=True)
class CandidateValidationGap:
    candidate_id: str
    missing_provider_diversity: int
    missing_source_diversity: int
    missing_temporal_diversity: int
    missing_positive_control: bool
    missing_negative_control: bool
    missing_unknown_control: bool
    scope_requirement: str
    provenance_requirement: str
    attribution_requirement: str
    validation_blockers: tuple[str, ...]


@dataclass(frozen=True)
class ValidationSourceCandidate:
    source_id: str
    provider_id: str
    url: str
    existing_local_raw: bool
    reacquirable: bool
    hardware_related_offer: bool
    explicit_inclusion_potential: bool
    explicit_exclusion_potential: bool
    genuinely_unknown_potential: bool
    attribution_quality: str
    temporal_continuity: str
    independent_provider: bool
    independent_source: bool
    validation_value: int
    score_breakdown: tuple[tuple[str, int], ...]
    acquisition_cost: str
    risk: str
    acquisition_method: str
    network_authorized: bool
    blocked: bool

    @classmethod
    def create(
        cls, *, source_id, provider_id, url, support_sources, support_providers,
        existing_local_raw, reacquirable, hardware_related_offer,
        explicit_inclusion_potential, explicit_exclusion_potential,
        genuinely_unknown_potential, attribution_quality, temporal_continuity,
        blocked=False, reusable_validation=True,
    ):
        independent_provider = provider_id not in support_providers
        independent_source = source_id not in support_sources
        breakdown = {
            "INDEPENDENT_PROVIDER": 5 if independent_provider else -8,
            "INDEPENDENT_SOURCE": 5 if independent_source else -8,
            "REPRODUCIBLE_LOCAL_RAW": 5 if existing_local_raw else 0,
            "CANDIDATE_SCOPE_MATCH": 4 if hardware_related_offer else -6,
            "EXPLICIT_CONTROL": 4 if explicit_inclusion_potential or explicit_exclusion_potential else 0,
            "UNKNOWN_CONTROL": 3 if genuinely_unknown_potential else 0,
            "OFFER_ATTRIBUTION": 3 if attribution_quality == "OFFER_EXACT" else -5,
            "TEMPORAL_CONTINUITY": 2 if temporal_continuity == "SNAPSHOT_HASHED" else -3,
            "REUSABLE_VALIDATION": 2 if reusable_validation else 0,
            "BLOCKED": -20 if blocked else 0,
        }
        value = sum(breakdown.values())
        method = "BLOCKED" if blocked else "LOCAL_REPLAY" if existing_local_raw else "HTTP"
        network = method == "HTTP" and reacquirable and value > 0
        return cls(
            source_id=source_id, provider_id=provider_id, url=url,
            existing_local_raw=existing_local_raw, reacquirable=reacquirable,
            hardware_related_offer=hardware_related_offer,
            explicit_inclusion_potential=explicit_inclusion_potential,
            explicit_exclusion_potential=explicit_exclusion_potential,
            genuinely_unknown_potential=genuinely_unknown_potential,
            attribution_quality=attribution_quality, temporal_continuity=temporal_continuity,
            independent_provider=independent_provider, independent_source=independent_source,
            validation_value=value, score_breakdown=tuple(sorted(breakdown.items())),
            acquisition_cost="ZERO_NETWORK" if existing_local_raw else "ONE_REQUEST",
            risk="LOW" if attribution_quality == "OFFER_EXACT" and temporal_continuity == "SNAPSHOT_HASHED" else "HIGH",
            acquisition_method=method, network_authorized=network, blocked=blocked,
        )


@dataclass(frozen=True)
class MinimalValidationAcquisitionSet:
    candidate_id: str
    actions: tuple[ValidationSourceCandidate, ...]
    expected_providers_gained: int
    expected_sources_gained: int
    expected_control_coverage: tuple[ValidationControlType, ...]
    expected_validation_blockers_remaining: tuple[str, ...]
    total_requests: int
    attribution_risk: str
    temporal_risk: str


@dataclass(frozen=True)
class CandidateValidationAcquisitionOutcome:
    action_id: str
    candidate_id: str
    source_id: str
    provider_id: str
    raw_document_path: str
    raw_document_hash: str
    acquisition_status: str
    control_type: ValidationControlType
    observation_id: str
    extracted_evidence: str
    attribution_status: str
    independent_provider: bool
    independent_source: bool
    validation_value: int
    provenance: str
    temporal_status: str
    source_url: str
    registered_raw_document_id: str
    compared_baseline_hash: str
    section: str
    nearby_price: str
    structural_locator: str
    unknown_reason: str | None


def minimum_validation_acquisition_set(gap, candidates):
    eligible = tuple(item for item in candidates if item.validation_value > 0 and not item.blocked)
    for size in range(1, len(eligible) + 1):
        valid = []
        for combo in combinations(eligible, size):
            providers = {item.provider_id for item in combo if item.independent_provider}
            sources = {item.source_id for item in combo if item.independent_source}
            controls = _controls(combo)
            if len(providers) < gap.missing_provider_diversity or len(sources) < gap.missing_source_diversity:
                continue
            if gap.missing_positive_control and ValidationControlType.EXPLICIT_INCLUDED not in controls:
                continue
            if gap.missing_negative_control and ValidationControlType.EXPLICIT_EXCLUDED not in controls:
                continue
            if gap.missing_unknown_control and ValidationControlType.GENUINELY_UNKNOWN not in controls:
                continue
            valid.append(combo)
        if valid:
            chosen = min(valid, key=lambda combo: (-sum(item.validation_value for item in combo), tuple(item.source_id for item in combo)))
            ordered = tuple(sorted(chosen, key=lambda item: item.source_id))
            return MinimalValidationAcquisitionSet(
                candidate_id=gap.candidate_id, actions=ordered,
                expected_providers_gained=len({item.provider_id for item in ordered}),
                expected_sources_gained=len({item.source_id for item in ordered}),
                expected_control_coverage=tuple(sorted(_controls(ordered), key=lambda item: item.value)),
                expected_validation_blockers_remaining=(),
                total_requests=sum(item.acquisition_method == "HTTP" for item in ordered),
                attribution_risk="LOW" if all(item.attribution_quality == "OFFER_EXACT" for item in ordered) else "HIGH",
                temporal_risk="LOW" if all(item.temporal_continuity == "SNAPSHOT_HASHED" for item in ordered) else "HIGH",
            )
    raise ValueError("No candidate set can close the explicit validation gap.")


def _controls(items):
    result = set()
    if any(item.explicit_inclusion_potential for item in items):
        result.add(ValidationControlType.EXPLICIT_INCLUDED)
    if any(item.explicit_exclusion_potential for item in items):
        result.add(ValidationControlType.EXPLICIT_EXCLUDED)
    if any(item.genuinely_unknown_potential for item in items):
        result.add(ValidationControlType.GENUINELY_UNKNOWN)
    return result
