from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from pathlib import Path

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_evidence_engine import CohortePricing


def _decimal(v: str) -> Decimal:
    return Decimal(str(v))


def load_cohortes(path: str | Path) -> list[CohortePricing]:
    out: list[CohortePricing] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            out.append(
                CohortePricing(
                    market=row["market"],
                    canonical_service=row["canonical_service"],
                    observations_n=int(row["observations_n"]),
                    providers_n=int(row["providers_n"]),
                    min_ars=_decimal(row["min_ars"]),
                    q1_ars=_decimal(row["q1_ars"]),
                    median_ars=_decimal(row["median_ars"]),
                    q3_ars=_decimal(row["q3_ars"]),
                    max_ars=_decimal(row["max_ars"]),
                    spread_ratio=_decimal(row["spread_ratio"]),
                    evidence_confidence=row["evidence_confidence"],
                    decision_ready=row["decision_ready"].upper() == "YES",
                    range_ready=row["range_ready"].upper() == "YES",
                )
            )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Natural language -> Enki pricing evidence/decision v1"
    )
    ap.add_argument("query")
    ap.add_argument(
        "--local-stats",
        default="data/local_pricing_stats_v1.csv",
    )
    ap.add_argument(
        "--remote-stats",
        default="data/remote_pricing_stats_v1.csv",
    )
    args = ap.parse_args()

    result = resolver_consulta_pricing(
        args.query,
        local_cohortes=load_cohortes(args.local_stats),
        remote_cohortes=load_cohortes(args.remote_stats),
    )
    p = result.parsed

    print("ENKI NATURAL LANGUAGE DECISION v1")
    print("=================================")
    print(f"Query:          {p.raw_text}")
    print(f"Status:         {result.status}")
    print(f"Intent:         {p.intent_action.value}")
    print(f"Side:           {p.intent_side.value}")
    print(f"Object:         {p.economic_object_kind.value}")
    print(
        "Service:        "
        + (" | ".join(p.canonical_services) if p.canonical_services else "UNKNOWN")
    )
    print(f"Market scope:   {p.market_scope.value}")
    print(f"Province:       {p.geography.province or 'UNKNOWN'}")
    print(f"Price:          {p.price.value if p.price.value is not None else 'NONE'}")
    print(f"Currency:       {p.price.currency}")

    if result.clarification_reason:
        print(f"Clarification:  {result.clarification_reason}")
    if result.clarification_question:
        print(f"Question:       {result.clarification_question}")
    if result.unsupported_reason:
        print(f"Unsupported:    {result.unsupported_reason}")

    e = result.evidence
    if e is not None:
        print()
        print("EVIDENCE")
        print("--------")
        print(f"Market:         {e.market}")
        print(f"Service:        {e.canonical_service}")
        print(f"Observations:   {e.observations_n}")
        print(f"Providers:      {e.providers_n}")
        print(f"Min ARS:        {e.min_ars}")
        print(f"Q1 ARS:         {e.q1_ars}")
        print(f"Median ARS:     {e.median_ars}")
        print(f"Q3 ARS:         {e.q3_ars}")
        print(f"Max ARS:        {e.max_ars}")
        print(f"Confidence:     {e.evidence_confidence}")
        if e.price_position:
            print(f"Price position: {e.price_position}")
        if e.decision_label:
            print(f"Decision:       {e.decision_label}")
        elif e.status == "RANGE_READY":
            print("Decision:       WITHHELD — range only")
        elif e.status == "INSUFFICIENT_EVIDENCE":
            print("Decision:       WITHHELD — insufficient evidence")
        elif e.status == "NO_EVIDENCE":
            print("Decision:       WITHHELD — no evidence")


if __name__ == "__main__":
    main()
