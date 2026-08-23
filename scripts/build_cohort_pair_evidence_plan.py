from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json

from src.infraestructura.cohort_pair_evidence_planner import build_cohort_pair_evidence_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build bilateral economic evidence plan for one cohort.")
    for name in (
        "normalization", "registry", "dimensions", "offer_evidence", "identities",
        "acquisitions", "audit", "pairs", "unlock_sets", "counterfactuals", "plan", "summary",
    ):
        parser.add_argument(name)
    parser.add_argument("--cohort", default="VISITA_TECNICA_DOMICILIO")
    args = parser.parse_args()
    metrics = build_cohort_pair_evidence_plan(
        args.normalization, args.registry, args.dimensions, args.offer_evidence,
        args.identities, args.acquisitions, args.audit, args.pairs,
        args.unlock_sets, args.counterfactuals, args.plan, args.summary,
        cohort=args.cohort,
    )
    print(json.dumps(metrics, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
