from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

from src.aplicacion.pricing_dimensions import (
    infer_commercial_context,
    infer_price_scope,
)
from src.aplicacion.runtime_cohort_lineage_gate import (
    RuntimeCohortBuild,
    build_runtime_cohort_rows,
)
from src.infraestructura.offer_evidence_artifact import load_offer_evidence_sidecar
from src.infraestructura.economic_dimensions_v2_artifact import (
    load_economic_dimensions_v2_sidecar,
)
from src.infraestructura.temporal_evidence_artifact import load_temporal_evidence


def _quantile_linear(values: list[float], q: float) -> float:
    """Deterministic linear interpolation on sorted values."""
    if not values:
        raise ValueError("values must not be empty")
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    weight = pos - lo
    return xs[lo] * (1 - weight) + xs[hi] * weight


def _build(rows: list[dict[str, str]], *, market_scope: str) -> list[dict[str, object]]:
    prices: dict[tuple[str, str, str, object], list[float]] = defaultdict(list)
    sources: dict[tuple[str, str, str, object], set[str]] = defaultdict(set)

    for row in rows:
        if row["semantic_role"] != "SINGLE_SERVICE":
            continue
        if row["market_scope"] != market_scope:
            continue
        if row["currency"] != "ARS":
            continue

        canonical = row["canonical_service"].strip()
        if not canonical:
            continue

        market = row["province"] if market_scope == "LOCAL_SERVICE" else "AR"
        try:
            price = float(row["price_value"])
        except (TypeError, ValueError):
            continue

        economic_object_raw = row.get("economic_object_raw", "")
        price_scope = infer_price_scope(economic_object_raw)
        commercial_context = infer_commercial_context(economic_object_raw)

        key = (market, canonical, price_scope, commercial_context)
        prices[key].append(price)
        sources[key].add(row["source"])

    result = []
    for (market, service, price_scope, commercial_context), vals in prices.items():
        vals = sorted(vals)
        n = len(vals)
        providers_n = len(sources[(market, service, price_scope, commercial_context)])
        q1 = _quantile_linear(vals, 0.25)
        median = statistics.median(vals)
        q3 = _quantile_linear(vals, 0.75)
        spread_ratio = max(vals) / min(vals) if min(vals) > 0 else float("inf")

        if n >= 5 and providers_n >= 3 and spread_ratio <= 2.5:
            confidence = "MEDIUM"
        elif n >= 3 and providers_n >= 2 and spread_ratio <= 2.0:
            confidence = "LOW"
        else:
            confidence = "INSUFFICIENT"

        result.append({
            "market": market,
            "canonical_service": service,
            "price_scope": price_scope,
            "commercial_context": commercial_context.value.value,
            "observations_n": n,
            "providers_n": providers_n,
            "min_ars": min(vals),
            "q1_ars": q1,
            "median_ars": median,
            "q3_ars": q3,
            "max_ars": max(vals),
            "spread_ratio": round(spread_ratio, 3),
            "evidence_confidence": confidence,
            "decision_ready": "YES" if confidence == "MEDIUM" else "NO",
            "range_ready": "YES" if confidence in {"LOW", "MEDIUM"} else "NO",
        })

    result.sort(
        key=lambda x: (x["observations_n"], x["providers_n"]),
        reverse=True,
    )
    return result


def _write(path: str | Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "market", "canonical_service", "price_scope", "commercial_context",
        "observations_n", "providers_n",
        "min_ars", "q1_ars", "median_ars", "q3_ars", "max_ars",
        "spread_ratio", "evidence_confidence", "decision_ready", "range_ready",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def _write_runtime(path: str | Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "market", "canonical_service", "price_scope", "commercial_context",
        "observations_n", "providers_n",
        "min_ars", "q1_ars", "median_ars", "q3_ars", "max_ars",
        "spread_ratio", "evidence_confidence", "decision_ready", "range_ready",
        "lineage_gate_version", "service_reach_gate_version",
        "temporal_gate_version", "temporal_state",
        "acquired_at_min", "acquired_at_max", "freshness_policy_version",
        "observation_ids",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_pricing_statistics(
    normalization_path: str | Path,
    *,
    local_out_path: str | Path,
    remote_out_path: str | Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Build local and remote pricing cohorts from semantic normalization CSV."""
    with Path(normalization_path).open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    local = _build(rows, market_scope="LOCAL_SERVICE")
    remote = _build(rows, market_scope="REMOTE_NATIONAL_SERVICE")
    _write(local_out_path, local)
    _write(remote_out_path, remote)
    return local, remote


def build_runtime_pricing_statistics(
    normalization_path: str | Path,
    lineage_path: str | Path,
    *,
    repository_root: str | Path,
    local_out_path: str | Path,
    remote_out_path: str | Path,
    dimensions_path: str | Path | None = None,
    temporal_path: str | Path | None = None,
) -> tuple[RuntimeCohortBuild, RuntimeCohortBuild]:
    """Build versioned runtime cohorts after fail-closed RAW lineage admission."""
    with Path(normalization_path).open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    evidence = load_offer_evidence_sidecar(lineage_path)
    dimensions = (
        load_economic_dimensions_v2_sidecar(dimensions_path)
        if dimensions_path is not None else None
    )
    temporal = load_temporal_evidence(temporal_path) if temporal_path is not None else None
    local = build_runtime_cohort_rows(
        rows,
        evidence,
        repository_root,
        market_scope="LOCAL_SERVICE",
        service_reach_dimensions=dimensions,
        temporal_evidence=temporal,
    )
    remote = build_runtime_cohort_rows(
        rows,
        evidence,
        repository_root,
        market_scope="REMOTE_NATIONAL_SERVICE",
        service_reach_dimensions=dimensions,
        temporal_evidence=temporal,
    )
    _write_runtime(local_out_path, list(local.cohorts))
    _write_runtime(remote_out_path, list(remote.cohorts))
    return local, remote


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalization", default="data/semantic_normalization_v4.csv")
    ap.add_argument("--local-out", default="data/local_pricing_stats_v1.csv")
    ap.add_argument("--remote-out", default="data/remote_pricing_stats_v1.csv")
    ap.add_argument(
        "--lineage",
        help="Offer evidence sidecar; enables the fail-closed runtime lineage gate.",
    )
    ap.add_argument("--repository-root", default=".")
    ap.add_argument(
        "--dimensions",
        help="Economic dimensions v2 sidecar; composes explicit service-reach admission.",
    )
    ap.add_argument(
        "--temporal",
        help="Temporal evidence sidecar; composes current-pricing admission.",
    )
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    if args.lineage:
        local_build, remote_build = build_runtime_pricing_statistics(
            args.normalization,
            args.lineage,
            repository_root=args.repository_root,
            local_out_path=args.local_out,
            remote_out_path=args.remote_out,
            dimensions_path=args.dimensions,
            temporal_path=args.temporal,
        )
        local = list(local_build.cohorts)
        remote = list(remote_build.cohorts)
    else:
        local, remote = build_pricing_statistics(
            args.normalization,
            local_out_path=args.local_out,
            remote_out_path=args.remote_out,
        )

    print("ENKI PRICING STATISTICS v1")
    print("==========================")
    print(f"Normalization: {args.normalization}")
    print(f"Local stats:   {args.local_out}")
    print(f"Remote stats:  {args.remote_out}")

    print("\nLOCAL")
    print("-----")
    for c in local[:args.top]:
        print(
            f'{c["market"]} :: {c["canonical_service"]} :: '
            f'{c["price_scope"]} :: {c["commercial_context"]} | '
            f'n={c["observations_n"]} providers={c["providers_n"]} | '
            f'min={c["min_ars"]:.0f} q1={c["q1_ars"]:.0f} '
            f'median={c["median_ars"]:.0f} q3={c["q3_ars"]:.0f} '
            f'max={c["max_ars"]:.0f} | '
            f'confidence={c["evidence_confidence"]} '
            f'decision_ready={c["decision_ready"]}'
        )

    print("\nREMOTE")
    print("------")
    for c in remote[:args.top]:
        print(
            f'{c["market"]} :: {c["canonical_service"]} :: '
            f'{c["price_scope"]} :: {c["commercial_context"]} | '
            f'n={c["observations_n"]} providers={c["providers_n"]} | '
            f'min={c["min_ars"]:.0f} q1={c["q1_ars"]:.0f} '
            f'median={c["median_ars"]:.0f} q3={c["q3_ars"]:.0f} '
            f'max={c["max_ars"]:.0f} | '
            f'confidence={c["evidence_confidence"]} '
            f'decision_ready={c["decision_ready"]}'
        )

    print("\nRULE")
    print("----")
    print("LOW/MEDIUM cohorts may expose empirical range.")
    print("Only MEDIUM cohorts are allowed to emit BAJO/RAZONABLE/ALTO in Decision v1.")


if __name__ == "__main__":
    main()
