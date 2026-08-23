from src.dominio.candidate_validation_acquisition import (
    CandidateValidationGap,
    ValidationControlType,
    ValidationSourceCandidate,
    minimum_validation_acquisition_set,
)


def source(name, provider, *, local=True, included=False, excluded=False, unknown=False, support=False, blocked=False):
    return ValidationSourceCandidate.create(
        source_id=name, provider_id=provider, url=f"https://{name}.test",
        support_sources=("support-source",), support_providers=("support-provider",),
        existing_local_raw=local, reacquirable=True, hardware_related_offer=True,
        explicit_inclusion_potential=included, explicit_exclusion_potential=excluded,
        genuinely_unknown_potential=unknown, attribution_quality="OFFER_EXACT",
        temporal_continuity="SNAPSHOT_HASHED", blocked=blocked,
    )


GAP = CandidateValidationGap(
    candidate_id="candidate:1", missing_provider_diversity=2, missing_source_diversity=2,
    missing_temporal_diversity=1, missing_positive_control=True,
    missing_negative_control=False, missing_unknown_control=True,
    scope_requirement="targeted_acquisition:v1",
    provenance_requirement="REPRODUCIBLE_RAW",
    attribution_requirement="OFFER_EXACT",
    validation_blockers=("INSUFFICIENT_IN_SCOPE_INDEPENDENT_HOLDOUT",),
)


def test_same_provider_or_source_is_not_independent_and_temporal_does_not_inflate():
    same_provider = source("new-source", "support-provider", unknown=True)
    same_source = source("support-source", "new-provider", unknown=True)

    assert same_provider.independent_provider is False
    assert same_provider.independent_source is True
    assert same_source.independent_provider is True
    assert same_source.independent_source is False


def test_new_provider_and_source_count_independently():
    item = source("new-source", "new-provider", unknown=True)

    assert item.independent_provider is True
    assert item.independent_source is True
    assert item.validation_value > 0


def test_local_raw_is_preferred_and_zero_value_never_authorizes_network():
    local = source("local", "provider:a", local=True, unknown=True)
    zero = source("support-source", "support-provider", local=False)

    assert local.acquisition_method == "LOCAL_REPLAY"
    assert local.network_authorized is False
    assert zero.validation_value <= 0
    assert zero.network_authorized is False


def test_positive_value_may_authorize_network_only_without_local_raw():
    item = source("remote", "provider:remote", local=False, included=True)

    assert item.validation_value > 0
    assert item.acquisition_method == "HTTP"
    assert item.network_authorized is True


def test_blocked_source_never_authorizes_bypass():
    item = source("blocked", "provider:blocked", local=False, included=True, blocked=True)

    assert item.network_authorized is False
    assert item.acquisition_method == "BLOCKED"


def test_minimum_set_uses_two_independent_sources_and_all_control_types():
    items = (
        source("jadetech", "provider:j", included=True, unknown=True),
        source("bitz", "provider:b", excluded=True, unknown=True),
        source("dmr", "provider:d", unknown=True),
    )
    plan = minimum_validation_acquisition_set(GAP, items)

    assert [item.source_id for item in plan.actions] == ["bitz", "jadetech"]
    assert plan.expected_providers_gained == 2
    assert plan.expected_sources_gained == 2
    assert set(plan.expected_control_coverage) == {
        ValidationControlType.EXPLICIT_INCLUDED,
        ValidationControlType.EXPLICIT_EXCLUDED,
        ValidationControlType.GENUINELY_UNKNOWN,
    }
    assert plan.expected_validation_blockers_remaining == ()
    assert plan.total_requests == 0
