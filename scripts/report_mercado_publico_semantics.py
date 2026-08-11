import argparse
import json
import sqlite3
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from src.aplicacion.caracterizador_mercado_publico import (
    clasificar_scope_tecnologico,
    explicar_consistencia_linea,
    explicar_consistencia_orden,
)

EXTRACTOR_VERSION = "mercado_publico_purchase_order_v1"


def main() -> None:
    parser = argparse.ArgumentParser(description="Characterize Mercado Publico economic semantics and technology scope.")
    parser.add_argument("--db", default="enki_mercado_publico_cl_sprint3.db")
    args = parser.parse_args()
    print(json.dumps(build_report(Path(args.db)), ensure_ascii=False, indent=2))


def build_report(db_path: Path) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    orders = con.execute(
        """
        SELECT o.*, rd.raw_content
        FROM mercado_publico_order_observations o
        JOIN raw_documents rd ON rd.id = o.raw_document_id
        WHERE o.extractor_version = ?
        ORDER BY o.id
        """,
        (EXTRACTOR_VERSION,),
    ).fetchall()
    lines = con.execute(
        "SELECT * FROM mercado_publico_line_item_observations WHERE extractor_version = ? ORDER BY id",
        (EXTRACTOR_VERSION,),
    ).fetchall()

    tech_counts: Counter[str] = Counter()
    tech_reasons: Counter[str] = Counter()
    line_consistency: Counter[str] = Counter()
    line_reasons: Counter[str] = Counter()
    order_consistency: Counter[str] = Counter()
    order_reasons: Counter[str] = Counter()
    category_prefixes: Counter[str] = Counter()
    tech_examples: list[dict[str, Any]] = []

    for line in lines:
        code = _loads(line["category_code_raw_json"])
        category = _loads(line["category_raw_json"])
        scope = clasificar_scope_tecnologico(code, category)
        tech_counts[scope.status] += 1
        tech_reasons[scope.reason] += 1
        category_prefixes[_prefix(code)] += 1
        if scope.status == "TECH_RELEVANT" and len(tech_examples) < 10:
            tech_examples.append(_line_example(line, scope.reason))

        consistency = explicar_consistencia_linea(
            quantity=_loads(line["quantity_raw_json"]),
            net_price=_loads(line["net_price_raw_json"]),
            line_total=_loads(line["total_raw_json"]),
        )
        line_consistency[consistency.status] += 1
        line_reasons[consistency.reason] += 1

    for order in orders:
        raw = json.loads(order["raw_content"])
        items = raw.get("Items", {}).get("Listado", []) if isinstance(raw.get("Items"), dict) else []
        sum_line_total = sum(float(item.get("Total") or 0) for item in items if isinstance(item, dict))
        consistency = explicar_consistencia_orden(
            order_total=raw.get("Total"),
            total_neto=raw.get("TotalNeto"),
            impuestos=raw.get("Impuestos"),
            cargos=raw.get("Cargos"),
            descuentos=raw.get("Descuentos"),
            sum_line_total=sum_line_total,
        )
        order_consistency[consistency.status] += 1
        order_reasons[consistency.reason] += 1

    return {
        "db": str(db_path),
        "orders": len(orders),
        "lines": len(lines),
        "source_semantics": {
            "PrecioNeto": "preserved as source item PrecioNeto; treated as net price field, not corrected or normalized",
            "line_Total": "preserved as source item Total; many records expose 0.0 even when quantity and PrecioNeto are positive",
            "order_Total": "preserved as source order Total; in mismatches it matches TotalNeto + Impuestos + Cargos - Descuentos",
            "classification": "CodigoCategoria/Categoria treated as official structured UNSPSC-derived classification from ChileCompra API docs",
        },
        "technology_scope": {
            "counts": dict(tech_counts),
            "reasons": dict(tech_reasons),
            "official_rule": "TECH_RELEVANT only when CodigoCategoria starts with UNSPSC 43 or 8111; missing/0 is UNKNOWN; other structured categories are NON_TECH",
            "category_prefixes": dict(category_prefixes),
            "tech_examples": tech_examples,
        },
        "economic_consistency": {
            "line_status": dict(line_consistency),
            "line_reasons": dict(line_reasons),
            "order_status": dict(order_consistency),
            "order_reasons": dict(order_reasons),
        },
        "line_distribution": _line_distribution(lines),
    }


def _line_distribution(lines: list[sqlite3.Row]) -> dict[str, Any]:
    by_order: Counter[int] = Counter(int(line["raw_document_id"]) for line in lines)
    values = list(by_order.values())
    return {
        "single_item_orders": sum(1 for value in values if value == 1),
        "multi_item_orders": sum(1 for value in values if value > 1),
        "min_lines_per_order": min(values) if values else 0,
        "max_lines_per_order": max(values) if values else 0,
        "median_lines_per_order": statistics.median(values) if values else 0,
    }


def _line_example(line: sqlite3.Row, reason: str) -> dict[str, Any]:
    return {
        "source_record_id": line["source_record_id"],
        "description": _loads(line["description_raw_json"]),
        "category_code": _loads(line["category_code_raw_json"]),
        "category": _loads(line["category_raw_json"]),
        "quantity": _loads(line["quantity_raw_json"]),
        "unit": _loads(line["unit_raw_json"]),
        "net_price": _loads(line["net_price_raw_json"]),
        "total": _loads(line["total_raw_json"]),
        "reason": reason,
    }


def _prefix(code: Any) -> str:
    value = str(code)
    return value[:2] if value and value != "UNKNOWN" else "UNKNOWN"


def _loads(value: str) -> Any:
    return json.loads(value)


if __name__ == "__main__":
    main()
