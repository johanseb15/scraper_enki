from __future__ import annotations
import argparse,csv
from decimal import Decimal
from pathlib import Path
from src.aplicacion.pricing_evidence_engine import CohortePricing,evaluar_precio

def D(v): return Decimal(str(v))

def load(path: str) -> list[CohortePricing]:
    out=[]
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            out.append(CohortePricing(
                market=r["market"], canonical_service=r["canonical_service"],
                observations_n=int(r["observations_n"]), providers_n=int(r["providers_n"]),
                min_ars=D(r["min_ars"]), q1_ars=D(r["q1_ars"]), median_ars=D(r["median_ars"]),
                q3_ars=D(r["q3_ars"]), max_ars=D(r["max_ars"]), spread_ratio=D(r["spread_ratio"]),
                evidence_confidence=r["evidence_confidence"], decision_ready=r["decision_ready"].upper()=="YES",
                range_ready=r["range_ready"].upper()=="YES", price_scope=(r.get("price_scope") or "UNKNOWN"),
                commercial_context=(r.get("commercial_context") or "STANDARD"),
            ))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--market-type",choices=("local","remote"),required=True)
    ap.add_argument("--province"); ap.add_argument("--service",required=True); ap.add_argument("--price",type=Decimal)
    ap.add_argument("--price-scope",choices=("UNKNOWN","PER_HOUR","PER_MONTH","PER_VISIT","PER_UNIT"),default="UNKNOWN")
    ap.add_argument("--commercial-context",choices=("STANDARD","URGENCY"),default="STANDARD")
    ap.add_argument("--local-stats",default="data/local_pricing_stats_v1.csv"); ap.add_argument("--remote-stats",default="data/remote_pricing_stats_v1.csv")
    a=ap.parse_args()
    if a.market_type=="local":
        if not a.province: raise SystemExit("--province is required for local services")
        market=a.province; path=a.local_stats
    else: market="AR"; path=a.remote_stats
    r=evaluar_precio(load(path),market=market,canonical_service=a.service,price_scope=a.price_scope,commercial_context=a.commercial_context,proposed_price_ars=a.price)
    print("ENKI DECISION EVIDENCE v1"); print("=========================")
    print(f"Status:       {r.status}"); print(f"Market:       {r.market}"); print(f"Service:      {r.canonical_service}")
    print(f"Price scope:  {r.price_scope}"); print(f"Context:      {r.commercial_context.value.value}")
    if r.status!="NO_EVIDENCE":
        print(f"Observations: {r.observations_n}"); print(f"Providers:    {r.providers_n}")
        print(f"Min ARS:      {r.min_ars}"); print(f"Q1 ARS:       {r.q1_ars}"); print(f"Median ARS:   {r.median_ars}")
        print(f"Q3 ARS:       {r.q3_ars}"); print(f"Max ARS:      {r.max_ars}"); print(f"Confidence:   {r.evidence_confidence}")
    if r.price_position: print(f"Price pos.:   {r.price_position}")
    if r.decision_label: print(f"Decision:     {r.decision_label}")
    if r.status=="RANGE_READY": print("Decision:     WITHHELD — cohort only supports empirical range")
    elif r.status=="INSUFFICIENT_EVIDENCE": print("Decision:     WITHHELD — insufficient evidence")
    elif r.status=="NO_EVIDENCE": print("Decision:     WITHHELD — no matching cohort")

if __name__=="__main__": main()
