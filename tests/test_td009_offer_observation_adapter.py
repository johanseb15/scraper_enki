from __future__ import annotations

import json
from pathlib import Path

from src.dominio.price_scope_contract import (
    BillingPeriodMeaning,
    ChargedUnitMeaning,
    PriceBoundMeaning,
)

from src.dominio.offer_observation import PriceExpressionIdentity
from src.infraestructura.offer_observation_adapter import (
    OfferObservationAdaptationStatus,
    adapt_legacy_offer_observation,
)


def _identity(
    *,
    observation_id="62",
    source="bairescloud_generic",
    raw_document_id="sha256:raw-a",
    offer_key="generic:4:backup|38000|ARS",
    status="RESOLVED",
):
    return {
        "schema_version": "offer-evidence-identity-v1",
        "observation_id": observation_id,
        "source": source,
        "raw_document_id": raw_document_id,
        "offer_key": offer_key,
        "extraction_path": "generic_price_extractor_v3/generic:4:backup",
        "status": status,
        "reason": "test",
    }


def _evidence(
    *,
    observation_id="62",
    source="bairescloud_generic",
    raw_document_id="sha256:raw-a",
):
    return {
        "schema_version": "offer-reach-charged-scope-evidence-v1",
        "observation_id": observation_id,
        "lineage": {
            "observation_id": observation_id,
            "source_id": source,
            "raw_document_id": raw_document_id,
        },
    }


def _price_expression():
    return PriceExpressionIdentity(
        price_value="38000",
        currency="ARS",
        charged_unit=ChargedUnitMeaning.UNIT,
        billing_period=BillingPeriodMeaning.UNKNOWN,
        price_bound=PriceBoundMeaning.EXACT,
    )


def test_matching_legacy_contracts_resolve_offer_observation():
    result = adapt_legacy_offer_observation(
        identity_row=_identity(),
        evidence_row=_evidence(),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price_expression(),
    )

    assert result.status is OfferObservationAdaptationStatus.RESOLVED
    assert result.observation is not None
    assert result.reason is None
    assert result.observation.source_observation_id == "62"
    assert result.observation.raw_document_id == "sha256:raw-a"


def test_unresolved_identity_stays_unresolved_without_fabrication():
    result = adapt_legacy_offer_observation(
        identity_row=_identity(
            raw_document_id=None,
            offer_key=None,
            status="UNRESOLVED",
        ),
        evidence_row=_evidence(),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price_expression(),
    )

    assert result.status is OfferObservationAdaptationStatus.UNRESOLVED
    assert result.observation is None


def test_raw_snapshot_disagreement_is_explicit_conflict():
    result = adapt_legacy_offer_observation(
        identity_row=_identity(raw_document_id="sha256:raw-a"),
        evidence_row=_evidence(raw_document_id="sha256:raw-b"),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price_expression(),
    )

    assert result.status is OfferObservationAdaptationStatus.CONFLICTED
    assert result.observation is None
    assert "RAW_DOCUMENT_ID_MISMATCH" in result.reason


def test_source_or_observation_disagreement_is_explicit_conflict():
    result = adapt_legacy_offer_observation(
        identity_row=_identity(observation_id="62"),
        evidence_row=_evidence(observation_id="68"),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price_expression(),
    )

    assert result.status is OfferObservationAdaptationStatus.CONFLICTED
    assert result.observation is None
    assert "OBSERVATION_ID_MISMATCH" in result.reason


def test_offer_key_price_suffix_is_not_part_of_logical_offer_identity():
    result = adapt_legacy_offer_observation(
        identity_row=_identity(
            offer_key="generic:4:backup-de-datos|38000|ARS",
        ),
        evidence_row=_evidence(),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price_expression(),
    )

    assert result.status is OfferObservationAdaptationStatus.RESOLVED
    assert result.observation.logical_offer_key == "generic:4:backup-de-datos"


def test_current_observation_62_is_not_silently_collapsed_across_raw_snapshots():
    root = Path(__file__).resolve().parents[1]

    identities = [
        json.loads(line)
        for line in (
            root / "data/offer_evidence_identities_v1.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    evidence = [
        json.loads(line)
        for line in (
            root / "data/offer_evidence_v1.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    identity_62 = next(
        row for row in identities
        if row["observation_id"] == "62"
    )
    evidence_62 = next(
        row for row in evidence
        if row["observation_id"] == "62"
    )

    result = adapt_legacy_offer_observation(
        identity_row=identity_62,
        evidence_row=evidence_62,
        raw_expression="BackUp de Datos cada 100gb Extras PC-Notebook-AIO",
        price_expression=_price_expression(),
    )

    assert result.status is OfferObservationAdaptationStatus.CONFLICTED
    assert result.observation is None
    assert "RAW_DOCUMENT_ID_MISMATCH" in result.reason
