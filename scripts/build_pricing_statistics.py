from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path


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


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    ).lower()


def infer_price_scope(economic_object_raw: str) -> str:
    """Infer only explicit economic cadence from preserved source text.

    Conservative rule: if cadence is not explicit, return UNKNOWN.
    Technical quantities/specifications such as 100GB or Windows 11 do not
    create cadence by themselves.
    """
    x = _fold(economic_object_raw)

    if re.search(
        r"\bx\s*1\s*(?:hs?|hora)\b"
        r"|\bpor\s+hora\b"
        r"|\bla\s+hora\b"
        r"|\bhora\s+(?:inicial|adicional|servicio|tecnica|tecnico)\b"
        r"|\bhora(?:s)?\s+de\s+(?:servicio|soporte|trabajo)\b",
        x,
    ):
        return "PER_HOUR"

    if re.search(
        r"\bpor\s+mes\b"
        r"|\bal\s+mes\b"
        r"|\bmensual(?:mente)?\b"
        r"|\babono\s+mensual\b",
        x,
    ):
        return "PER_MONTH"

    if re.search(r"\bpor\s+visita\b|\bcada\s+visita\b", x):
        return "PER_VISIT"

    if re.search(
        r"\bpor\s+(?:equipo|unidad|pc|notebook|camara)\b"
        r"|\bcada\s+\d+(?:[.,]\d+)?\s*(?:gb|tb)\b",
        x,
    ):
        return "PER_UNIT"

    return "UNKNOWN"


def infer_commercial_context(economic_object_raw: str) -> str:
    """Identify only explicit exceptional commercial conditions."""
    x = _fold(economic_object_raw)
    if re.search(
        r"\burgenc(?:ia|ias)\b"
        r"|\bfuera\s+de\s+horario\b"
        r"|\bfin(?:es)?\s+de\s+semana\b"
        r"|\bferiado(?:s)?\b",
        x,
    ):
        return "URGENCY"
    return "STANDARD"


def _build(rows: list[dict[str, str]], *, market_scope: str) -> list[dict[str, object]]:
    prices: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    sources: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)

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
            "commercial_context": commercial_context,
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalization", default="data/semantic_normalization_v4.csv")
    ap.add_argument("--local-out", default="data/local_pricing_stats_v1.csv")
    ap.add_argument("--remote-out", default="data/remote_pricing_stats_v1.csv")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

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
