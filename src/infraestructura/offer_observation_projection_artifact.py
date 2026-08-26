from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import csv
import json
from pathlib import Path
from typing import Iterable

from src.dominio.offer_observation import PriceExpressionIdentity
from src.dominio.price_scope_contract import normalize_price_scope
from src.infraestructura.artifact_lifecycle import (
    ArtifactClass,
    build_manifest,
    write_manifest,
)

from src.infraestructura.offer_snapshot_projection import (
    OfferSnapshotProjection,
    OfferSnapshotProjectionStatus,
    project_legacy_offer_snapshots,
)


SCHEMA_VERSION = "offer-observation-projection-v1"


def build_offer_observation_projection_bundle(
    *,
    root: str | Path,
    output_dir: str | Path,
) -> dict[str, int]:
    root_path = Path(root).resolve()
    output = Path(output_dir)

    normalization_path = (
        root_path / "data/semantic_normalization_v4.csv"
    )
    identities_path = (
        root_path / "data/offer_evidence_identities_v1.jsonl"
    )
    evidence_path = (
        root_path / "data/offer_evidence_v1.jsonl"
    )

    with normalization_path.open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        normalization = {
            row["observation_id"]: row
            for row in csv.DictReader(handle)
        }

    identities = _read_jsonl(identities_path)

    evidence = {
        row["observation_id"]: row
        for row in _read_jsonl(evidence_path)
    }

    projection_rows: list[OfferSnapshotProjection] = []

    for identity in identities:
        observation_id = str(
            identity.get("observation_id") or ""
        ).strip()

        normalized = normalization.get(observation_id)
        evidence_row = evidence.get(observation_id)

        if normalized is None:
            raise ValueError(
                "Missing semantic normalization row for "
                f"observation_id={observation_id}."
            )

        if evidence_row is None:
            raise ValueError(
                "Missing offer evidence row for "
                f"observation_id={observation_id}."
            )

        raw_expression = (
            normalized.get("economic_object_raw") or ""
        )
        price_value = normalized.get("price_value") or ""
        currency = normalized.get("currency") or ""

        scope = normalize_price_scope(
            raw_expression,
            has_price=bool(price_value),
            provenance=(
                "offer-observation-projection:"
                f"observation_id={observation_id}"
            ),
        )

        price_expression = PriceExpressionIdentity(
            price_value=price_value,
            currency=currency,
            charged_unit=scope.charged_unit,
            billing_period=scope.billing_period,
            price_bound=scope.price_bound,
        )

        projection_rows.extend(
            project_legacy_offer_snapshots(
                identity_row=identity,
                evidence_row=evidence_row,
                raw_expression=raw_expression,
                price_expression=price_expression,
            )
        )

    artifact_path = (
        output / "offer_observations_v1.jsonl"
    )

    metrics = build_offer_observation_projection_artifact(
        rows=projection_rows,
        output_path=artifact_path,
    )

    manifest = build_manifest(
        root=root_path,
        artifact_class=ArtifactClass.DETERMINISTIC_DERIVED,
        generator_path=root_path
        / "src/infraestructura/"
        "offer_observation_projection_artifact.py",
        input_paths=(
            normalization_path,
            identities_path,
            evidence_path,
        ),
        output_path=artifact_path,
    )

    write_manifest(
        output / "offer_observations_manifest_v1.json",
        manifest,
        root=root_path,
    )

    return metrics


@dataclass(frozen=True)
class OfferObservationProjectionArtifactRow:
    projection_id: str
    source_observation_id: str
    source_id: str
    raw_document_id: str
    provenance_kind: str
    status: str
    reason: str | None
    logical_offer_id: str | None
    price_expression_id: str | None
    snapshot_observation_id: str | None


def build_offer_observation_projection_artifact(
    *,
    rows: Iterable[OfferSnapshotProjection],
    output_path: str | Path,
) -> dict[str, int]:
    payloads = [
        _projection_payload(row)
        for row in rows
    ]

    payloads.sort(
        key=lambda item: (
            item["source_id"],
            item["source_observation_id"],
            item["raw_document_id"],
            item["projection_id"],
        )
    )

    projection_ids = [
        item["projection_id"]
        for item in payloads
    ]

    if len(projection_ids) != len(set(projection_ids)):
        raise ValueError(
            "Offer observation projection requires unique projection_id values."
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for payload in payloads:
            handle.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )

    resolved = sum(
        item["status"]
        == OfferSnapshotProjectionStatus.RESOLVED.value
        for item in payloads
    )

    unresolved = sum(
        item["status"]
        == OfferSnapshotProjectionStatus.UNRESOLVED.value
        for item in payloads
    )

    return {
        "TOTAL_ROWS": len(payloads),
        "RESOLVED": resolved,
        "UNRESOLVED": unresolved,
    }


def load_offer_observation_projection_artifact(
    path: str | Path,
) -> dict[str, OfferObservationProjectionArtifactRow]:
    result: dict[
        str,
        OfferObservationProjectionArtifactRow,
    ] = {}

    source = Path(path)

    for line_number, line in enumerate(
        source.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not line.strip():
            continue

        payload = json.loads(line)

        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                "Unsupported offer observation projection schema "
                f"at line {line_number}."
            )

        projection_id = _clean(
            payload.get("projection_id")
        )

        if not projection_id:
            raise ValueError(
                "Missing projection_id "
                f"at line {line_number}."
            )

        if projection_id in result:
            raise ValueError(
                "Duplicate projection_id "
                f"at line {line_number}: {projection_id}"
            )

        row = OfferObservationProjectionArtifactRow(
            projection_id=projection_id,
            source_observation_id=_required(
                payload,
                "source_observation_id",
                line_number,
            ),
            source_id=_required(
                payload,
                "source_id",
                line_number,
            ),
            raw_document_id=_required(
                payload,
                "raw_document_id",
                line_number,
            ),
            provenance_kind=_required(
                payload,
                "provenance_kind",
                line_number,
            ),
            status=_required(
                payload,
                "status",
                line_number,
            ),
            reason=_optional(payload.get("reason")),
            logical_offer_id=_optional(
                payload.get("logical_offer_id")
            ),
            price_expression_id=_optional(
                payload.get("price_expression_id")
            ),
            snapshot_observation_id=_optional(
                payload.get("snapshot_observation_id")
            ),
        )

        _validate_loaded_row(
            row,
            line_number=line_number,
        )

        expected_projection_id = _projection_id(
            source_id=row.source_id,
            source_observation_id=row.source_observation_id,
            raw_document_id=row.raw_document_id,
        )

        if row.projection_id != expected_projection_id:
            raise ValueError(
                "projection_id does not match projection identity "
                f"at line {line_number}."
            )

        result[projection_id] = row

    return result


def _projection_payload(
    row: OfferSnapshotProjection,
) -> dict[str, object]:
    projection_id = _projection_id(
        source_id=row.source_id,
        source_observation_id=row.source_observation_id,
        raw_document_id=row.raw_document_id,
    )

    observation = row.observation

    if (
        row.status
        is OfferSnapshotProjectionStatus.RESOLVED
    ):
        if observation is None:
            raise ValueError(
                "Resolved projection requires OfferObservation."
            )

        logical_offer_id = observation.logical_offer_id
        price_expression_id = observation.price_expression_id
        snapshot_observation_id = (
            observation.snapshot_observation_id
        )
    else:
        if observation is not None:
            raise ValueError(
                "Unresolved projection cannot carry strong "
                "OfferObservation identity."
            )

        logical_offer_id = None
        price_expression_id = None
        snapshot_observation_id = None

    return {
        "schema_version": SCHEMA_VERSION,
        "projection_id": projection_id,
        "source_observation_id": row.source_observation_id,
        "source_id": row.source_id,
        "raw_document_id": row.raw_document_id,
        "provenance_kind": row.provenance_kind,
        "status": row.status.value,
        "reason": row.reason,
        "logical_offer_id": logical_offer_id,
        "price_expression_id": price_expression_id,
        "snapshot_observation_id": snapshot_observation_id,
    }


def _projection_id(
    *,
    source_id: str,
    source_observation_id: str,
    raw_document_id: str,
) -> str:
    payload = {
        "source_id": _clean(source_id),
        "source_observation_id": _clean(
            source_observation_id
        ),
        "raw_document_id": _clean(raw_document_id),
    }

    if not all(payload.values()):
        raise ValueError(
            "Projection identity requires source_id, "
            "source_observation_id and raw_document_id."
        )

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return (
        "offer-projection:"
        + sha256(encoded).hexdigest()
    )


def _validate_loaded_row(
    row: OfferObservationProjectionArtifactRow,
    *,
    line_number: int,
) -> None:
    if row.status == OfferSnapshotProjectionStatus.RESOLVED.value:
        if not all((
            row.logical_offer_id,
            row.price_expression_id,
            row.snapshot_observation_id,
        )):
            raise ValueError(
                "Resolved projection missing strong identity "
                f"at line {line_number}."
            )
        return

    if row.status == OfferSnapshotProjectionStatus.UNRESOLVED.value:
        if any((
            row.logical_offer_id,
            row.price_expression_id,
            row.snapshot_observation_id,
        )):
            raise ValueError(
                "Unresolved projection fabricates strong identity "
                f"at line {line_number}."
            )
        return

    raise ValueError(
        "Unknown projection status "
        f"at line {line_number}: {row.status}"
    )


def _required(
    payload: dict,
    key: str,
    line_number: int,
) -> str:
    value = _clean(payload.get(key))
    if not value:
        raise ValueError(
            f"Missing {key} at line {line_number}."
        )
    return value


def _optional(value: object) -> str | None:
    cleaned = _clean(value)
    return cleaned or None


def _clean(value: object) -> str:
    return str(value or "").strip()



def _read_jsonl(path: str | Path) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
