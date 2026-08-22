from __future__ import annotations

import argparse
import json

from src.infraestructura.evidence_acquisition_planner import build_target_dossier_and_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build near-comparable dossier, counterfactual unlocks and acquisition plan.")
    parser.add_argument("normalization")
    parser.add_argument("registry")
    parser.add_argument("dimensions")
    parser.add_argument("gaps")
    parser.add_argument("shadow")
    parser.add_argument("dossier")
    parser.add_argument("unlocks")
    parser.add_argument("plan")
    args = parser.parse_args()
    metrics = build_target_dossier_and_plan(args.normalization, args.registry, args.dimensions, args.gaps, args.shadow, args.dossier, args.unlocks, args.plan)
    for key, value in metrics.items():
        print(f"{key}={json.dumps(value, ensure_ascii=False, sort_keys=True)}")


if __name__ == "__main__":
    main()
