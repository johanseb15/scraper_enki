import argparse
import json
import sqlite3
from statistics import median
from typing import Any

UNKNOWN_JSON = {'"UNKNOWN"', 'null', '[]', '{}'}


def main() -> None:
    parser = argparse.ArgumentParser(description="USASpending cohort market activity readout.")
    parser.add_argument("--db", default="datos.db")
    parser.add_argument("--extractor-version", default="usaspending_award_v1")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM usaspending_award_observations WHERE extractor_version = ? ORDER BY id",
        (args.extractor_version,),
    ).fetchall()
    observations = [dict(row) for row in rows]
    payload = build_readout(observations, top=args.top)
    print(json.dumps(payload, ensure_ascii=False))


def build_readout(rows: list[dict[str, Any]], top: int = 10) -> dict[str, Any]:
    amounts = [_num(_loads(row["award_amount_raw_json"])) for row in rows]
    numeric_amounts = [amount for amount in amounts if amount is not None]
    positives = [amount for amount in numeric_amounts if amount > 0]
    return {
        "cohort_definition": "USASpending awards acquired with NAICS 541511, 541512, 541513, 541519; contract award types A/B/C/D; sorted by Award Amount desc. Cohort statistics only, not market size or benchmark.",
        "total_awards": len(rows),
        "award_amount_distribution": {
            "total_observed_award_amount": sum(numeric_amounts),
            "median_award_amount": median(numeric_amounts) if numeric_amounts else "UNKNOWN",
            "min_award_amount": min(numeric_amounts) if numeric_amounts else "UNKNOWN",
            "max_award_amount": max(numeric_amounts) if numeric_amounts else "UNKNOWN",
            "zero_awards": sum(1 for amount in numeric_amounts if amount == 0),
            "negative_awards": sum(1 for amount in numeric_amounts if amount < 0),
        },
        "top_naics_by_count": _top_group(rows, "naics_raw_json", top, by_amount=False),
        "top_naics_by_observed_award_amount": _top_group(rows, "naics_raw_json", top, by_amount=True),
        "top_psc_by_count": _top_group(rows, "psc_raw_json", top, by_amount=False),
        "top_psc_by_observed_award_amount": _top_group(rows, "psc_raw_json", top, by_amount=True),
        "top_agencies_by_count": _top_group(rows, "awarding_agency_raw_json", top, by_amount=False),
        "top_agencies_by_observed_award_amount": _top_group(rows, "awarding_agency_raw_json", top, by_amount=True),
        "top_recipients_by_count": _top_group(rows, "recipient_raw_json", top, by_amount=False),
        "top_recipients_by_observed_award_amount": _top_group(rows, "recipient_raw_json", top, by_amount=True),
        "time_distribution_by_start_month": _time_distribution(rows),
        "geography_place_of_performance": _geo_distribution(rows, top),
        "largest_awards": _extreme_awards(rows, top, largest=True),
        "smallest_positive_awards": _extreme_awards(rows, top, largest=False, positive_only=True),
        "description_quality_syntactic": _description_quality(rows),
    }


def _top_group(rows: list[dict[str, Any]], field: str, top: int, by_amount: bool) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = _label(_loads(row[field]))
        amount = _num(_loads(row["award_amount_raw_json"])) or 0
        item = groups.setdefault(key, {"key": key, "award_count": 0, "observed_award_amount": 0.0})
        item["award_count"] += 1
        item["observed_award_amount"] += amount
    sort_key = "observed_award_amount" if by_amount else "award_count"
    return sorted(groups.values(), key=lambda item: item[sort_key], reverse=True)[:top]


def _time_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, int] = {}
    for row in rows:
        value = _loads(row["start_date_raw_json"])
        key = value[:7] if isinstance(value, str) and len(value) >= 7 else "UNKNOWN"
        groups[key] = groups.get(key, 0) + 1
    return [{"month": key, "award_count": groups[key]} for key in sorted(groups)]


def _geo_distribution(rows: list[dict[str, Any]], top: int) -> list[dict[str, Any]]:
    groups: dict[str, int] = {}
    for row in rows:
        value = _loads(row["place_of_performance_raw_json"])
        if isinstance(value, dict):
            key = f"{value.get('country', 'UNKNOWN')}:{value.get('state', 'UNKNOWN')}"
        else:
            key = _label(value)
        groups[key] = groups.get(key, 0) + 1
    return sorted(({"place": k, "award_count": v} for k, v in groups.items()), key=lambda item: item["award_count"], reverse=True)[:top]


def _extreme_awards(rows: list[dict[str, Any]], top: int, largest: bool, positive_only: bool = False) -> list[dict[str, Any]]:
    items = []
    for row in rows:
        amount = _num(_loads(row["award_amount_raw_json"]))
        if amount is None or (positive_only and amount <= 0):
            continue
        items.append({
            "award_id": _loads(row["metadata_json"]).get("award_id_raw", "UNKNOWN"),
            "source_record_id": row["source_record_id"],
            "recipient": _loads(row["recipient_raw_json"]),
            "agency": _loads(row["awarding_agency_raw_json"]),
            "description": _loads(row["description_raw_json"]),
            "amount": amount,
            "NAICS": _loads(row["naics_raw_json"]),
            "PSC": _loads(row["psc_raw_json"]),
        })
    return sorted(items, key=lambda item: item["amount"], reverse=largest)[:top]


def _description_quality(rows: list[dict[str, Any]]) -> dict[str, int]:
    out = {"empty": 0, "short_lt_20": 0, "normal_gte_20": 0}
    for row in rows:
        value = _loads(row["description_raw_json"])
        text = "" if value == "UNKNOWN" else str(value)
        if len(text) == 0:
            out["empty"] += 1
        elif len(text) < 20:
            out["short_lt_20"] += 1
        else:
            out["normal_gte_20"] += 1
    return out


def _label(value: Any) -> str:
    if isinstance(value, dict):
        code = value.get("code") or value.get("state") or value.get("country")
        desc = value.get("description")
        return f"{code} - {desc}" if desc else str(code or value)
    return str(value)


def _loads(value: str) -> Any:
    return json.loads(value)


def _num(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


if __name__ == "__main__":
    main()
