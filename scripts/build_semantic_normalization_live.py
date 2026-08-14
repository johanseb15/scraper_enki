from __future__ import annotations

import argparse

from src.aplicacion.semantic_normalization_live import (
    build_semantic_rows,
    write_semantic_csv,
)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Extiende la normalización semántica congelada v4 sobre una DB live "
            "sin reescribir semántica histórica."
        )
    )
    ap.add_argument("--db", required=True)
    ap.add_argument(
        "--baseline",
        default="data/semantic_normalization_v4.csv",
    )
    ap.add_argument(
        "--out",
        default="data/semantic_normalization_live_v1.csv",
    )
    args = ap.parse_args()

    rows, reused, newly_classified = build_semantic_rows(
        args.db,
        baseline_path=args.baseline,
    )
    write_semantic_csv(args.out, rows)

    roles: dict[str, int] = {}
    markets: dict[str, int] = {}
    canonicals: dict[str, int] = {}

    for row in rows:
        roles[row["semantic_role"]] = roles.get(row["semantic_role"], 0) + 1
        markets[row["market_scope"]] = markets.get(row["market_scope"], 0) + 1
        canonical = row["canonical_service"]
        if canonical:
            canonicals[canonical] = canonicals.get(canonical, 0) + 1

    print()
    print("ENKI SEMANTIC NORMALIZATION LIVE v1")
    print("===================================")
    print(f"Rows exported:       {len(rows)}")
    print(f"Frozen v4 reused:    {reused}")
    print(f"Newly classified:    {newly_classified}")
    print(f"Output:              {args.out}")

    print("\nSEMANTIC ROLES")
    print("--------------")
    for name, n in sorted(roles.items(), key=lambda x: (-x[1], x[0])):
        print(f"{name}: {n}")

    print("\nMARKET SCOPES")
    print("-------------")
    for name, n in sorted(markets.items(), key=lambda x: (-x[1], x[0])):
        print(f"{name}: {n}")

    print("\nNEW OBSERVATIONS")
    print("----------------")
    baseline_ids = set()
    # Rows with ids beyond frozen-v4 count are not assumed to be new.
    # Print classifications that did not come from the baseline by testing
    # whether their exact v4 economic identity was absent in build step is
    # intentionally summarized only by count here. Detailed CSV is source truth.

    print(f"Classified outside frozen v4: {newly_classified}")


if __name__ == "__main__":
    main()
