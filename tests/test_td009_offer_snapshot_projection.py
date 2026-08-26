from __future__ import annotations

from src.dominio.offer_observation import PriceExpressionIdentity
from src.dominio.price_scope_contract import (
    BillingPeriodMeaning,
    ChargedUnitMeaning,
    PriceBoundMeaning,
)
from src.infraestructura.offer_snapshot_projection import (
    OfferSnapshotProjectionStatus,
    project_legacy_offer_snapshots,
)


def _price():
    return PriceExpressionIdentity(
        price_value="38000",
        currency="ARS",
        charged_unit=ChargedUnitMeaning.UNIT,
        billing_period=BillingPeriodMeaning.UNKNOWN,
        price_bound=PriceBoundMeaning.EXACT,
    )


def _identity(raw_document_id="sha256:reacquired"):
    return {
        "schema_version": "offer-evidence-identity-v1",
        "observation_id": "62",
        "source": "bairescloud_generic",
        "raw_document_id": raw_document_id,
        "offer_key": "generic:4:backup|38000|ARS",
        "extraction_path": "generic_price_extractor_v3/generic:4:backup",
        "status": "RESOLVED",
        "reason": "Exact source/object/price/currency match.",
    }


def _evidence(raw_document_id="sha256:historical"):
    return {
        "schema_version": "offer-reach-charged-scope-evidence-v1",
        "observation_id": "62",
        "lineage": {
            "observation_id": "62",
            "source_id": "bairescloud_generic",
            "raw_document_id": raw_document_id,
            "provenance": "tests/fixtures/bairescloud.html",
        },
        "claims": [],
    }


def test_distinct_raw_snapshots_are_preserved_as_distinct_projection_rows():
    rows = project_legacy_offer_snapshots(
        identity_row=_identity(),
        evidence_row=_evidence(),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price(),
    )

    assert len(rows) == 2
    assert {row.raw_document_id for row in rows} == {
        "sha256:reacquired",
        "sha256:historical",
    }


def test_reacquired_snapshot_with_exact_offer_identity_is_resolved():
    rows = project_legacy_offer_snapshots(
        identity_row=_identity(),
        evidence_row=_evidence(),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price(),
    )

    reacquired = next(
        row for row in rows
        if row.raw_document_id == "sha256:reacquired"
    )

    assert reacquired.status is OfferSnapshotProjectionStatus.RESOLVED
    assert reacquired.observation is not None
    assert reacquired.observation.logical_offer_key == "generic:4:backup"
    assert reacquired.provenance_kind == "TARGETED_EXACT_OFFER_IDENTITY"


def test_historical_snapshot_without_offer_key_is_preserved_but_not_fabricated():
    rows = project_legacy_offer_snapshots(
        identity_row=_identity(),
        evidence_row=_evidence(),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price(),
    )

    historical = next(
        row for row in rows
        if row.raw_document_id == "sha256:historical"
    )

    assert historical.status is OfferSnapshotProjectionStatus.UNRESOLVED
    assert historical.observation is None
    assert historical.reason == "MISSING_LOGICAL_OFFER_IDENTITY"
    assert historical.provenance_kind == "HISTORICAL_OFFER_EVIDENCE"


def test_same_raw_snapshot_is_deduplicated_not_duplicated():
    rows = project_legacy_offer_snapshots(
        identity_row=_identity(raw_document_id="sha256:same"),
        evidence_row=_evidence(raw_document_id="sha256:same"),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price(),
    )

    assert len(rows) == 1
    assert rows[0].raw_document_id == "sha256:same"
    assert rows[0].status is OfferSnapshotProjectionStatus.RESOLVED


def test_unresolved_targeted_identity_does_not_create_fake_snapshot():
    identity = _identity(raw_document_id=None)
    identity["offer_key"] = None
    identity["status"] = "UNRESOLVED"

    rows = project_legacy_offer_snapshots(
        identity_row=identity,
        evidence_row=_evidence(),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price(),
    )

    assert len(rows) == 1
    assert rows[0].raw_document_id == "sha256:historical"
    assert rows[0].status is OfferSnapshotProjectionStatus.UNRESOLVED


def test_missing_raw_on_historical_evidence_does_not_fabricate_snapshot():
    rows = project_legacy_offer_snapshots(
        identity_row=_identity(),
        evidence_row=_evidence(raw_document_id=None),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price(),
    )

    assert len(rows) == 1
    assert rows[0].raw_document_id == "sha256:reacquired"
    assert rows[0].status is OfferSnapshotProjectionStatus.RESOLVED


def test_every_projection_row_preserves_legacy_observation_anchor():
    rows = project_legacy_offer_snapshots(
        identity_row=_identity(),
        evidence_row=_evidence(),
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price(),
    )

    assert {row.source_observation_id for row in rows} == {"62"}
