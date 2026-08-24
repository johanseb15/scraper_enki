from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse,csv,json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.pricing_evidence_engine import CohortePricing
def D(v): return Decimal(str(v))
def load(path):
    out=[]
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            out.append(CohortePricing(market=r["market"],canonical_service=r["canonical_service"],observations_n=int(r["observations_n"]),providers_n=int(r["providers_n"]),min_ars=D(r["min_ars"]),q1_ars=D(r["q1_ars"]),median_ars=D(r["median_ars"]),q3_ars=D(r["q3_ars"]),max_ars=D(r["max_ars"]),spread_ratio=D(r["spread_ratio"]),evidence_confidence=r["evidence_confidence"],decision_ready=r["decision_ready"].upper()=="YES",range_ready=r["range_ready"].upper()=="YES",price_scope=(r.get("price_scope") or "UNKNOWN"),commercial_context=(r.get("commercial_context") or "STANDARD")))
    return out
def fields(result):
    p=result.parsed; ps=result.evidence.price_scope if result.evidence else (p.price.type.value if p.price.type.value in {"PER_HOUR","PER_MONTH","PER_VISIT","PER_UNIT"} else "UNKNOWN")
    return {"intent_action":p.intent_action.value,"intent_side":p.intent_side.value,"economic_object_kind":p.economic_object_kind.value,"canonical_services":list(p.canonical_services),"market_scope":p.market_scope.value,"modality":p.modality.value,"price_value":p.price.value,"currency":p.price.currency,"price_scope":ps,"province":p.geography.province,"city":p.geography.city,"condition":p.condition,"parts_scope":p.commercial_context.parts_scope.value}
def same(e,a):
    if isinstance(e,(int,float)) and isinstance(a,(int,float)): return abs(float(e)-float(a))<1e-9
    return e==a
def classify(record,result):
    a=record["adjudication"]; b=a["expected_behavior"]; expected_status=a.get("expected_resolution_status")
    if result.status=="DECISION_READY" and not a.get("allow_decision",False): return "UNSAFE_DECISION",["unexpected DECISION_READY"]
    if b=="CLARIFICATION" and result.status!="CLARIFICATION_REQUIRED": return "WRONG_INTERPRETATION",[f"expected CLARIFICATION_REQUIRED, got {result.status}"]
    if b=="SAFE_UNSUPPORTED" and result.status!="UNSUPPORTED_QUERY": return "WRONG_INTERPRETATION",[f"expected UNSUPPORTED_QUERY, got {result.status}"]
    if b=="PARSE":
        if result.status in {"CLARIFICATION_REQUIRED","UNSUPPORTED_QUERY"}:
            return "WRONG_INTERPRETATION",[f"expected evidence path, got {result.status}"]
        if expected_status and result.status!=expected_status:
            if (
                expected_status in {"RANGE_READY","DECISION_READY"}
                and result.status in {"INSUFFICIENT_EVIDENCE","NO_EVIDENCE"}
            ):
                return "EXPECTED_SAFETY_CHANGE",[]
            return "WRONG_INTERPRETATION",[f"expected {expected_status}, got {result.status}"]
    actual=fields(result); errors=[]
    for k,e in a.get("expected_fields",{}).items():
        if k not in actual: errors.append(f"unsupported expected field: {k}")
        elif not same(e,actual[k]): errors.append(f"{k}: expected={e!r} actual={actual[k]!r}")
    if errors:return "WRONG_INTERPRETATION",errors
    return ({"CLARIFICATION":"CLARIFICATION_CORRECT","SAFE_UNSUPPORTED":"SAFE_UNSUPPORTED","PARSE":"PARSE_CORRECT"}[b],[])
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--corpus",default="data/language/real_query_corpus_v1.jsonl"); ap.add_argument("--local-stats",required=True); ap.add_argument("--remote-stats",required=True); ap.add_argument("--out", required=True); x=ap.parse_args()
    local,remote=load(x.local_stats),load(x.remote_stats); rows=[]; c=Counter()
    for line in Path(x.corpus).read_text(encoding="utf-8").splitlines():
        if not line.strip():continue
        r=json.loads(line); result=resolver_consulta_pricing(r["query_raw"],local_cohortes=local,remote_cohortes=remote,language_evidence_type=r["provenance"]); outcome,errs=classify(r,result); c[outcome]+=1; rows.append({"id":r["id"],"provenance":r["provenance"],"query_raw":r["query_raw"],"actual_status":result.status,"audit_outcome":outcome,"errors":" | ".join(errs)})
    out=Path(x.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["id","provenance","query_raw","actual_status","audit_outcome","errors"]); w.writeheader(); w.writerows(rows)
    print("ENKI REAL QUERY CORPUS v1"); print("========================="); print(f"Cases: {len(rows)}")
    for k in ["PARSE_CORRECT","CLARIFICATION_CORRECT","SAFE_UNSUPPORTED","EXPECTED_SAFETY_CHANGE","WRONG_INTERPRETATION","UNSAFE_DECISION"]: print(f"{k}: {c[k]}")
    print(f"Audit: {out}")
if __name__=="__main__": main()
