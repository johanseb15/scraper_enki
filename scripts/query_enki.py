from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import csv
from decimal import Decimal
from pathlib import Path

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.enki_pricing_response import presentar_resultado_pricing
from src.aplicacion.pricing_evidence_engine import CohortePricing


def _decimal(v: str) -> Decimal:
    return Decimal(str(v))


def load_cohortes(path: str | Path) -> list[CohortePricing]:
    out: list[CohortePricing] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            out.append(CohortePricing(
                market=row["market"], canonical_service=row["canonical_service"],
                observations_n=int(row["observations_n"]), providers_n=int(row["providers_n"]),
                min_ars=_decimal(row["min_ars"]), q1_ars=_decimal(row["q1_ars"]), median_ars=_decimal(row["median_ars"]),
                q3_ars=_decimal(row["q3_ars"]), max_ars=_decimal(row["max_ars"]), spread_ratio=_decimal(row["spread_ratio"]),
                evidence_confidence=row["evidence_confidence"], decision_ready=row["decision_ready"].upper()=="YES",
                range_ready=row["range_ready"].upper()=="YES", price_scope=(row.get("price_scope") or "UNKNOWN"),
                commercial_context=(row.get("commercial_context") or "STANDARD"),
            ))
    return out


def main() -> None:
    ap=argparse.ArgumentParser(description="Natural language -> Enki pricing decision v1")
    ap.add_argument("query"); ap.add_argument("--local-stats",default="data/local_pricing_stats_v1.csv"); ap.add_argument("--remote-stats",default="data/remote_pricing_stats_v1.csv")
    ap.add_argument("--debug",action="store_true",help="Show parsed/evidence internals after the user-facing response.")
    args=ap.parse_args()
    result=resolver_consulta_pricing(args.query,local_cohortes=load_cohortes(args.local_stats),remote_cohortes=load_cohortes(args.remote_stats))
    response=presentar_resultado_pricing(result)
    print("ENKI"); print("===="); print(response.headline); print(response.summary)
    if response.evidence_line: print(response.evidence_line)
    if response.caveat: print(response.caveat)
    if args.debug:
        p=result.parsed; print(); print("DEBUG"); print("-----")
        print(f"status={result.status}"); print(f"intent={p.intent_action.value}"); print(f"side={p.intent_side.value}"); print(f"object={p.economic_object_kind.value}")
        print(f"services={p.canonical_services}"); print(f"market_scope={p.market_scope.value}"); print(f"province={p.geography.province}")
        print(f"price={p.price.value}"); print(f"price_type={p.price.type.value}"); print(f"currency={p.price.currency}")
        if result.clarification_reason: print(f"clarification_reason={result.clarification_reason}")
        if result.evidence:
            e=result.evidence; print(f"market={e.market}"); print(f"price_scope={e.price_scope}"); print(f"commercial_context={e.commercial_context.value.value}")
            print(f"confidence={e.evidence_confidence}"); print(f"decision={e.decision_label}")

if __name__=="__main__": main()
