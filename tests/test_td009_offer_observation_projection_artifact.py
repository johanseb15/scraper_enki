from __future__ import annotations

import json
from pathlib import Path

from src.dominio.offer_observation import PriceExpressionIdentity
from src.dominio.price_scope_contract import (
    BillingPeriodMeaning,
    ChargedUnitMeaning,
    PriceBoundMeaning,
)
from src.infraestructura.offer_observation_projection_artifact import (
    build_offer_observation_projection_artifact,
    load_offer_observation_projection_artifact,
)
from src.infraestructura.offer_snapshot_projection import (
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


def _rows():
    identity = {
        "schema_version": "offer-evidence-identity-v1",
        "observation_id": "62",
        "source": "bairescloud_generic",
        "raw_document_id": "sha256:reacquired",
        "offer_key": "generic:4:backup|38000|ARS",
        "extraction_path": "generic_price_extractor_v3/generic:4:backup",
        "status": "RESOLVED",
        "reason": "Exact source/object/price/currency match.",
    }

    evidence = {
        "schema_version": "offer-reach-charged-scope-evidence-v1",
        "observation_id": "62",
        "lineage": {
            "observation_id": "62",
            "source_id": "bairescloud_generic",
            "raw_document_id": "sha256:historical",
            "provenance": "tests/fixtures/bairescloud.html",
        },
        "claims": [],
    }

    return project_legacy_offer_snapshots(
        identity_row=identity,
        evidence_row=evidence,
        raw_expression="BackUp de Datos cada 100gb",
        price_expression=_price(),
    )


def test_artifact_writes_one_row_per_projection_snapshot(tmp_path):
    output = tmp_path / "offer_observations_v1.jsonl"

    metrics = build_offer_observation_projection_artifact(
        rows=_rows(),
        output_path=output,
    )

    payloads = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(payloads) == 2
    assert metrics["TOTAL_ROWS"] == 2
    assert metrics["RESOLVED"] == 1
    assert metrics["UNRESOLVED"] == 1


def test_projection_id_is_stable_and_unique_per_legacy_snapshot(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"

    build_offer_observation_projection_artifact(
        rows=_rows(),
        output_path=first,
    )
    build_offer_observation_projection_artifact(
        rows=reversed(_rows()),
        output_path=second,
    )

    assert first.read_bytes() == second.read_bytes()

    payloads = [
        json.loads(line)
        for line in first.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    projection_ids = [row["projection_id"] for row in payloads]

    assert len(projection_ids) == len(set(projection_ids))


def test_resolved_row_contains_strong_domain_identity(tmp_path):
    output = tmp_path / "artifact.jsonl"

    build_offer_observation_projection_artifact(
        rows=_rows(),
        output_path=output,
    )

    payloads = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    resolved = next(
        row for row in payloads
        if row["status"] == "RESOLVED"
    )

    assert resolved["logical_offer_id"]
    assert resolved["price_expression_id"]
    assert resolved["snapshot_observation_id"]


def test_unresolved_row_does_not_fabricate_strong_identity(tmp_path):
    output = tmp_path / "artifact.jsonl"

    build_offer_observation_projection_artifact(
        rows=_rows(),
        output_path=output,
    )

    payloads = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    unresolved = next(
        row for row in payloads
        if row["status"] == "UNRESOLVED"
    )

    assert unresolved["logical_offer_id"] is None
    assert unresolved["price_expression_id"] is None
    assert unresolved["snapshot_observation_id"] is None
    assert unresolved["reason"] == "MISSING_LOGICAL_OFFER_IDENTITY"


def test_loader_round_trips_artifact(tmp_path):
    output = tmp_path / "artifact.jsonl"

    build_offer_observation_projection_artifact(
        rows=_rows(),
        output_path=output,
    )

    loaded = load_offer_observation_projection_artifact(output)

    assert len(loaded) == 2
    assert {
        row.source_observation_id
        for row in loaded.values()
    } == {"62"}


def test_loader_rejects_duplicate_projection_id(tmp_path):
    output = tmp_path / "bad.jsonl"

    build_offer_observation_projection_artifact(
        rows=_rows(),
        output_path=output,
    )

    lines = output.read_text(encoding="utf-8").splitlines()
    output.write_text(
        lines[0] + "\n" + lines[0] + "\n",
        encoding="utf-8",
    )

    import pytest

    with pytest.raises(ValueError):
        load_offer_observation_projection_artifact(output)

from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    DimensionStatus,
    DimensionValue,
    EconomicEvidenceDimensionsV2,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.infraestructura.offer_snapshot_projection import (
    OfferSnapshotProjection,
    OfferSnapshotProjectionStatus,
)


def _raw_claim(value, raw_document_id):
    return DimensionClaim(
        value=value,
        origin=DimensionOrigin.RAW_SOURCE_OBSERVATION,
        provenance=KnowledgeProvenance(
            "RAW_SOURCE_EXPRESSION",
            f"raw_document_id={raw_document_id};field=economic_object_raw",
            "test-v1",
        ),
        raw_basis="raw basis",
    )


def _normalized_claim(value):
    return DimensionClaim(
        value=value,
        origin=DimensionOrigin.NORMALIZED_FIELD,
        provenance=KnowledgeProvenance(
            "SEMANTIC_NORMALIZATION_FIELD",
            "artifact=semantic_normalization_v4",
            "semantic-normalization-v4",
        ),
        raw_basis="normalized field",
    )


def _dimensions(raw_document_id="sha256:reacquired"):
    return EconomicEvidenceDimensionsV2(
        price_scope=DimensionValue(
            value="PER_UNIT",
            status=DimensionStatus.OBSERVED,
            claims=(
                _raw_claim("PER_UNIT", raw_document_id),
            ),
        ),
        currency=DimensionValue(
            value="ARS",
            status=DimensionStatus.INFERRED,
            claims=(
                _normalized_claim("ARS"),
            ),
        ),
    )


def _resolved_projection_with_dimensions():
    row = next(
        item for item in _rows()
        if item.status is OfferSnapshotProjectionStatus.RESOLVED
    )
    observation = row.observation
    assert observation is not None
    return OfferSnapshotProjection(
        source_observation_id=row.source_observation_id,
        source_id=row.source_id,
        raw_document_id=row.raw_document_id,
        provenance_kind=row.provenance_kind,
        status=row.status,
        observation=observation,
        reason=row.reason,
        economic_dimensions=_dimensions(row.raw_document_id),
    )


def test_artifact_serializes_snapshot_economic_dimensions(tmp_path):
    output = tmp_path / "artifact.jsonl"

    build_offer_observation_projection_artifact(
        rows=(_resolved_projection_with_dimensions(),),
        output_path=output,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["economic_dimensions"]["price_scope"]["status"] == "OBSERVED"
    assert payload["economic_dimensions"]["price_scope"]["value"] == "PER_UNIT"
    assert payload["economic_dimensions"]["currency"]["status"] == "INFERRED"


def test_loader_round_trips_snapshot_economic_dimensions(tmp_path):
    output = tmp_path / "artifact.jsonl"

    build_offer_observation_projection_artifact(
        rows=(_resolved_projection_with_dimensions(),),
        output_path=output,
    )

    loaded = next(iter(load_offer_observation_projection_artifact(output).values()))

    assert loaded.economic_dimensions is not None
    assert loaded.economic_dimensions.price_scope.status is DimensionStatus.OBSERVED
    assert loaded.economic_dimensions.price_scope.value == "PER_UNIT"
    assert loaded.economic_dimensions.currency.status is DimensionStatus.INFERRED


def test_loader_accepts_legacy_projection_without_dimensions(tmp_path):
    output = tmp_path / "legacy.jsonl"

    build_offer_observation_projection_artifact(
        rows=_rows(),
        output_path=output,
    )

    payloads = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for payload in payloads:
        payload.pop("economic_dimensions", None)

    output.write_text(
        "\n".join(
            json.dumps(payload, ensure_ascii=False, sort_keys=True)
            for payload in payloads
        ) + "\n",
        encoding="utf-8",
    )

    loaded = load_offer_observation_projection_artifact(output)

    assert loaded
    assert all(row.economic_dimensions is None for row in loaded.values())
