from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable

from src.dominio.price_scope_contract import ScopeCompatibility, compare_price_scopes
from src.dominio.commercial_context import (
    CommercialContext,
    CommercialContextCompatibility,
    CommercialContextOrigin,
    compare_commercial_contexts,
    commercial_context_from_value,
)


@dataclass(frozen=True)
class CohortePricing:
    market: str
    canonical_service: str
    observations_n: int
    providers_n: int
    min_ars: Decimal
    q1_ars: Decimal
    median_ars: Decimal
    q3_ars: Decimal
    max_ars: Decimal
    spread_ratio: Decimal
    evidence_confidence: str
    decision_ready: bool
    range_ready: bool
    price_scope: str = "UNKNOWN"
    commercial_context: CommercialContext | str = field(
        default_factory=lambda: commercial_context_from_value(
            None,
            origin=CommercialContextOrigin.CONTROLLED_FIXTURE,
        )
    )
    lineage_gate_version: str | None = None
    service_reach_gate_version: str | None = None
    temporal_gate_version: str | None = None
    temporal_state: str | None = None
    acquired_at_min: str | None = None
    acquired_at_max: str | None = None
    freshness_policy_version: str | None = None
    observation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.commercial_context, CommercialContext):
            object.__setattr__(
                self,
                "commercial_context",
                commercial_context_from_value(
                    self.commercial_context,
                    origin=CommercialContextOrigin.CONTROLLED_FIXTURE,
                ),
            )

    @property
    def evidence_id(self) -> str:
        return (
            f"pricing-cohort:{self.market}:{self.canonical_service}:"
            f"{self.price_scope}:{self.commercial_context.value.value}"
        )


@dataclass(frozen=True)
class ResultadoEvidenciaPrecio:
    status: str
    market: str
    canonical_service: str
    observations_n: int = 0
    providers_n: int = 0
    min_ars: Decimal | None = None
    q1_ars: Decimal | None = None
    median_ars: Decimal | None = None
    q3_ars: Decimal | None = None
    max_ars: Decimal | None = None
    evidence_confidence: str = "NONE"
    price_position: str | None = None
    decision_label: str | None = None
    evidence_id: str | None = None
    price_scope: str = "UNKNOWN"
    commercial_context: CommercialContext = field(
        default_factory=lambda: commercial_context_from_value(
            None,
            origin=CommercialContextOrigin.USER_CLAIM,
        )
    )
    evidence_commercial_context: CommercialContext | None = None
    lineage_gate_version: str | None = None
    service_reach_gate_version: str | None = None
    temporal_gate_version: str | None = None
    temporal_state: str | None = None
    acquired_at_min: str | None = None
    acquired_at_max: str | None = None
    freshness_policy_version: str | None = None
    observation_ids: tuple[str, ...] = ()


def evaluar_precio(
    cohortes: Iterable[CohortePricing],
    *,
    market: str,
    canonical_service: str,
    proposed_price_ars: Decimal | None = None,
    price_scope: str | None = None,
    commercial_context: CommercialContext | str | None = None,
) -> ResultadoEvidenciaPrecio:
    query_context = commercial_context_from_value(
        commercial_context,
        origin=CommercialContextOrigin.USER_CLAIM,
    )
    cohort = next(
        (
            c for c in cohortes
            if c.market == market
            and c.canonical_service == canonical_service
            and (
                price_scope is None
                or compare_price_scopes(c.price_scope, price_scope) is ScopeCompatibility.COMPATIBLE
            )
            and compare_commercial_contexts(
                c.commercial_context,
                query_context,
            ) is CommercialContextCompatibility.COMPATIBLE
        ),
        None,
    )

    if cohort is None:
        return ResultadoEvidenciaPrecio(
            status="NO_EVIDENCE",
            market=market,
            canonical_service=canonical_service,
            price_scope=price_scope or "UNKNOWN",
            commercial_context=query_context,
        )

    common = dict(
        market=market,
        canonical_service=canonical_service,
        observations_n=cohort.observations_n,
        providers_n=cohort.providers_n,
        min_ars=cohort.min_ars,
        q1_ars=cohort.q1_ars,
        median_ars=cohort.median_ars,
        q3_ars=cohort.q3_ars,
        max_ars=cohort.max_ars,
        evidence_confidence=cohort.evidence_confidence,
        evidence_id=cohort.evidence_id,
        price_scope=cohort.price_scope,
        commercial_context=query_context,
        evidence_commercial_context=cohort.commercial_context,
        lineage_gate_version=cohort.lineage_gate_version,
        service_reach_gate_version=cohort.service_reach_gate_version,
        temporal_gate_version=cohort.temporal_gate_version,
        temporal_state=cohort.temporal_state,
        acquired_at_min=cohort.acquired_at_min,
        acquired_at_max=cohort.acquired_at_max,
        freshness_policy_version=cohort.freshness_policy_version,
        observation_ids=cohort.observation_ids,
    )

    if not cohort.range_ready:
        return ResultadoEvidenciaPrecio(status="INSUFFICIENT_EVIDENCE", **common)

    price_position = None
    if proposed_price_ars is not None:
        if proposed_price_ars < cohort.min_ars:
            price_position = "BELOW_OBSERVED_RANGE"
        elif proposed_price_ars > cohort.max_ars:
            price_position = "ABOVE_OBSERVED_RANGE"
        else:
            price_position = "WITHIN_OBSERVED_RANGE"

    if not cohort.decision_ready or proposed_price_ars is None:
        return ResultadoEvidenciaPrecio(
            status="RANGE_READY",
            price_position=price_position,
            **common,
        )

    if proposed_price_ars < cohort.q1_ars:
        decision = "BAJO"
    elif proposed_price_ars > cohort.q3_ars:
        decision = "ALTO"
    else:
        decision = "RAZONABLE"

    return ResultadoEvidenciaPrecio(
        status="DECISION_READY",
        price_position=price_position,
        decision_label=decision,
        **common,
    )
