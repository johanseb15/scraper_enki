from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


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


def evaluar_precio(
    cohortes: Iterable[CohortePricing],
    *,
    market: str,
    canonical_service: str,
    proposed_price_ars: Decimal | None = None,
) -> ResultadoEvidenciaPrecio:
    cohort = next(
        (
            c for c in cohortes
            if c.market == market
            and c.canonical_service == canonical_service
        ),
        None,
    )

    if cohort is None:
        return ResultadoEvidenciaPrecio(
            status="NO_EVIDENCE",
            market=market,
            canonical_service=canonical_service,
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
    )

    if not cohort.range_ready:
        return ResultadoEvidenciaPrecio(
            status="INSUFFICIENT_EVIDENCE",
            **common,
        )

    price_position = None
    if proposed_price_ars is not None:
        if proposed_price_ars < cohort.min_ars:
            price_position = "BELOW_OBSERVED_RANGE"
        elif proposed_price_ars > cohort.max_ars:
            price_position = "ABOVE_OBSERVED_RANGE"
        else:
            price_position = "WITHIN_OBSERVED_RANGE"

    # Critical guardrail:
    # LOW-confidence cohorts may show range but may NOT emit BAJO/RAZONABLE/ALTO.
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
