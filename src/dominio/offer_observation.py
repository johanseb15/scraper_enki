from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from src.dominio.price_scope_contract import (
    BillingPeriodMeaning,
    ChargedUnitMeaning,
    PriceBoundMeaning,
)


class OfferObservationIdentityConflict(ValueError):
    """Legacy observation id points to incompatible concrete snapshots."""


def _clean(value: str | None) -> str:
    return str(value or "").strip()


def _stable_id(prefix: str, payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{prefix}:{sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class PriceExpressionIdentity:
    price_value: str
    currency: str
    charged_unit: ChargedUnitMeaning
    billing_period: BillingPeriodMeaning
    price_bound: PriceBoundMeaning

    def __post_init__(self) -> None:
        if not _clean(self.price_value):
            raise ValueError("PriceExpressionIdentity requires price_value.")
        if not _clean(self.currency):
            raise ValueError("PriceExpressionIdentity requires currency.")

    def identity_payload(self) -> dict[str, object]:
        return {
            "price_value": _clean(self.price_value),
            "currency": _clean(self.currency),
            "charged_unit": self.charged_unit.value,
            "billing_period": self.billing_period.value,
            "price_bound": self.price_bound.value,
        }


@dataclass(frozen=True)
class OfferObservation:
    source_observation_id: str
    source_id: str
    logical_offer_key: str
    raw_document_id: str
    raw_expression: str
    price_expression: PriceExpressionIdentity
    logical_offer_id: str
    price_expression_id: str
    snapshot_observation_id: str

    @classmethod
    def create(
        cls,
        *,
        source_observation_id: str,
        source_id: str,
        logical_offer_key: str,
        raw_document_id: str,
        raw_expression: str,
        price_expression: PriceExpressionIdentity,
    ) -> "OfferObservation":
        source_observation_id = _clean(source_observation_id)
        source_id = _clean(source_id)
        logical_offer_key = _clean(logical_offer_key)
        raw_document_id = _clean(raw_document_id)
        raw_expression = _clean(raw_expression)

        if not source_observation_id:
            raise ValueError("OfferObservation requires source_observation_id.")
        if not source_id:
            raise ValueError("OfferObservation requires source_id.")
        if not logical_offer_key:
            raise ValueError("OfferObservation requires logical_offer_key.")
        if not raw_document_id:
            raise ValueError("OfferObservation requires raw_document_id.")
        if not raw_expression:
            raise ValueError("OfferObservation requires raw_expression.")

        logical_offer_id = _stable_id(
            "offer",
            {
                "source_id": source_id,
                "logical_offer_key": logical_offer_key,
            },
        )

        price_expression_id = _stable_id(
            "price-expression",
            {
                "logical_offer_id": logical_offer_id,
                **price_expression.identity_payload(),
            },
        )

        snapshot_observation_id = _stable_id(
            "offer-observation",
            {
                "logical_offer_id": logical_offer_id,
                "raw_document_id": raw_document_id,
                "price_expression_id": price_expression_id,
            },
        )

        return cls(
            source_observation_id=source_observation_id,
            source_id=source_id,
            logical_offer_key=logical_offer_key,
            raw_document_id=raw_document_id,
            raw_expression=raw_expression,
            price_expression=price_expression,
            logical_offer_id=logical_offer_id,
            price_expression_id=price_expression_id,
            snapshot_observation_id=snapshot_observation_id,
        )

    @staticmethod
    def assert_legacy_identity_compatible(
        first: "OfferObservation",
        second: "OfferObservation",
    ) -> None:
        if first.source_observation_id != second.source_observation_id:
            return

        if first.snapshot_observation_id != second.snapshot_observation_id:
            raise OfferObservationIdentityConflict(
                "Legacy source_observation_id resolves to multiple concrete "
                "offer snapshots."
            )
