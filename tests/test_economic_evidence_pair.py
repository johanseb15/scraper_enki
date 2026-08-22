from collections import Counter

from src.dominio.economic_evidence_pair import PairCompatibilityState
from src.infraestructura.cohort_pair_evidence_planner import (
    build_pair_counterfactuals,
    evaluate_pair,
)


def audit(observation_id, provider, *, unknown=(), source=None, temporal="CURRENT_EXACT_OFFER", **values):
    defaults = {
        "currency": "ARS",
        "bundle_status": "SIMPLE",
        "price_scope": "PER_HOUR",
        "delivery_mode": "ONSITE",
        "geographic_reach": "CITY:Córdoba",
        "commercial_context": ["STANDARD"],
        "device_scope": ["PC"],
        "hardware_included": False,
        "materials_included": False,
    }
    defaults.update(values)
    dimensions = {
        name: {"status": "UNKNOWN" if name in unknown else "OBSERVED", "value": None if name in unknown else value}
        for name, value in defaults.items()
    }
    return {
        "observation_id": str(observation_id),
        "canonical_service": "VISITA_TECNICA_DOMICILIO",
        "semantic_role": "SINGLE_SERVICE",
        "semantic_status": "FULLY_REPRESENTED",
        "provider_id": provider,
        "source": source or provider,
        "source_url": f"https://{source or provider}.test",
        "price": "100",
        "dimensions": dimensions,
        "temporal_status": temporal,
        "provenance": f"raw:{observation_id}",
    }


def test_bilateral_missing_claims_and_multistep_counterfactual_are_explicit():
    pair, unlock = evaluate_pair(
        audit(1, "a", unknown=("geographic_reach",)),
        audit(2, "b", unknown=("commercial_context",)),
    )
    assert pair.compatibility_state is PairCompatibilityState.MISSING_EVIDENCE
    assert [item.claim_id for item in unlock.required_claims] == [
        "1:geographic_reach", "2:commercial_context"
    ]
    steps = build_pair_counterfactuals(pair)
    assert steps[0]["potentially_comparable"] is False
    assert steps[0]["remaining_missing_claims"] == ["2:commercial_context"]
    assert steps[-1]["potentially_comparable"] is True


def test_unknown_is_insufficient_but_known_incompatibility_is_mismatch():
    missing, _ = evaluate_pair(
        audit(1, "a", unknown=("device_scope",)), audit(2, "b")
    )
    mismatch, _ = evaluate_pair(
        audit(1, "a", device_scope=["NOTEBOOK"]), audit(2, "b", device_scope=["PC"])
    )
    assert missing.compatibility_state is PairCompatibilityState.MISSING_EVIDENCE
    assert not missing.explicit_mismatches
    assert mismatch.compatibility_state is PairCompatibilityState.EXPLICIT_MISMATCH
    assert mismatch.explicit_mismatches == ("DEVICE_SCOPE_MISMATCH",)


def test_hard_currency_conflict_same_provider_and_temporal_mismatch_never_unlock():
    conflicted = audit(1, "a")
    conflicted["dimensions"]["currency"] = {"status": "CONFLICTED", "value": None}
    currency, _ = evaluate_pair(conflicted, audit(2, "b"))
    same, _ = evaluate_pair(audit(1, "a"), audit(2, "a"))
    temporal, _ = evaluate_pair(
        audit(1, "a", temporal="TEMPORAL_MISMATCH"), audit(2, "b")
    )
    assert "CURRENCY_CONFLICT" in currency.hard_blockers
    assert "SAME_PROVIDER_NOT_INDEPENDENT" in same.hard_blockers
    assert "TEMPORAL_MISMATCH" in temporal.hard_blockers
    assert all(not build_pair_counterfactuals(pair)[-1]["potentially_comparable"] for pair in (currency, same, temporal))


def test_delivery_and_context_mismatches_preserve_exact_semantics():
    delivery, _ = evaluate_pair(
        audit(1, "a", delivery_mode="REMOTE"), audit(2, "b", delivery_mode="ONSITE")
    )
    compatible_context, _ = evaluate_pair(
        audit(1, "a", commercial_context=["URGENCY", "AFTER_HOURS"]),
        audit(2, "b", commercial_context=["AFTER_HOURS", "URGENCY"]),
    )
    mismatch_context, _ = evaluate_pair(
        audit(1, "a", commercial_context=["URGENCY"]),
        audit(2, "b", commercial_context=["STANDARD"]),
    )
    assert delivery.explicit_mismatches == ("DELIVERY_MODE_MISMATCH",)
    assert compatible_context.compatibility_state is PairCompatibilityState.COMPARABLE
    assert mismatch_context.explicit_mismatches == ("COMMERCIAL_CONTEXT_MISMATCH",)


def test_bundle_and_hardware_service_boundaries_are_hard():
    composite, _ = evaluate_pair(
        audit(1, "a", bundle_status="COMPOSITE"), audit(2, "b")
    )
    hardware = audit(1, "a"); hardware["semantic_role"] = "HARDWARE_PRODUCT"
    boundary, _ = evaluate_pair(hardware, audit(2, "b"))
    assert "BUNDLE_INCOMPATIBILITY" in composite.hard_blockers
    assert "HARDWARE_SERVICE_BOUNDARY" in boundary.hard_blockers


def test_pair_minimal_set_and_score_are_deterministic():
    left = audit(1, "a", unknown=("geographic_reach", "commercial_context"), source="shared")
    right = audit(2, "b", unknown=("commercial_context",), source="peer")
    one = evaluate_pair(left, right, source_counts=Counter({"shared": 2, "peer": 1}))
    two = evaluate_pair(left, right, source_counts=Counter({"shared": 2, "peer": 1}))
    assert one == two
    assert sum(dict(one[0].score_breakdown).values()) == one[0].score
