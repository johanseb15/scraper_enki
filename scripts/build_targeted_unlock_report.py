from __future__ import annotations

import argparse
import json

from src.infraestructura.targeted_unlock_report import build_targeted_unlock_report


def main():
    parser = argparse.ArgumentParser()
    for name in ("before_shadow", "after_shadow", "before_gap", "after_gap", "claims", "outcomes", "report"):
        parser.add_argument(name)
    args = parser.parse_args()
    metrics = build_targeted_unlock_report(args.before_shadow, args.after_shadow, args.before_gap, args.after_gap, args.claims, args.outcomes, args.report)
    for key, value in metrics.items(): print(f"{key}={json.dumps(value)}")


if __name__ == "__main__":
    main()
