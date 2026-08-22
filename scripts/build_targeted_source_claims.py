from __future__ import annotations

import argparse
import json

from src.infraestructura.targeted_claims_artifact import build_targeted_claims


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve exact offer identity and extract temporally safe targeted claims.")
    for name in ("normalization", "registry", "plan", "acquisitions", "claims", "identities", "outcomes", "rejected_claims"):
        parser.add_argument(name)
    args = parser.parse_args()
    metrics = build_targeted_claims(args.normalization, args.registry, args.plan, args.acquisitions, args.claims, args.identities, args.outcomes, args.rejected_claims)
    for key, value in metrics.items(): print(f"{key}={json.dumps(value, ensure_ascii=False, sort_keys=True)}")


if __name__ == "__main__":
    main()
