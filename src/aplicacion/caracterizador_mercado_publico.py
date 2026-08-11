from dataclasses import dataclass
from typing import Any

UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ScopeTecnologico:
    status: str
    reason: str
    category_code_raw: Any
    category_raw: Any


@dataclass(frozen=True)
class ConsistenciaLinea:
    status: str
    reason: str
    expected_quantity_x_net_price: float | str
    observed_total: float | str


@dataclass(frozen=True)
class ConsistenciaOrden:
    status: str
    reason: str
    expected_header_total: float | str
    observed_order_total: float | str
    observed_sum_line_total: float | str


def clasificar_scope_tecnologico(category_code_raw: Any, category_raw: Any) -> ScopeTecnologico:
    code = _code(category_code_raw)
    if code in ("", "0", UNKNOWN):
        return ScopeTecnologico("UNKNOWN", "MISSING_OR_UNKNOWN_OFFICIAL_CLASSIFICATION", category_code_raw, category_raw)
    if code.startswith("43"):
        return ScopeTecnologico("TECH_RELEVANT", "UNSPSC_43_IT_BROADCAST_TELECOM", category_code_raw, category_raw)
    if code.startswith("8111"):
        return ScopeTecnologico("TECH_RELEVANT", "UNSPSC_8111_COMPUTER_SERVICES", category_code_raw, category_raw)
    return ScopeTecnologico("NON_TECH", "UNSPSC_STRUCTURED_NON_TECH", category_code_raw, category_raw)


def explicar_consistencia_linea(quantity: Any, net_price: Any, line_total: Any) -> ConsistenciaLinea:
    values = [_number(quantity), _number(net_price), _number(line_total)]
    if any(value is None for value in values):
        return ConsistenciaLinea("NOT_EVALUABLE", "MISSING_OR_NON_NUMERIC_LINE_ECONOMICS", UNKNOWN, _number(line_total) or UNKNOWN)
    qty, price, total = values
    expected = qty * price
    if abs(expected - total) < 0.01:
        return ConsistenciaLinea("MATCH", "QUANTITY_X_NET_PRICE_MATCHES_LINE_TOTAL", expected, total)
    if total == 0 and expected > 0:
        return ConsistenciaLinea("MISMATCH", "LINE_TOTAL_ZERO_BUT_QUANTITY_X_NET_PRICE_POSITIVE", expected, total)
    return ConsistenciaLinea("MISMATCH", "LINE_TOTAL_DIFFERS_FROM_QUANTITY_X_NET_PRICE", expected, total)


def explicar_consistencia_orden(
    *,
    order_total: Any,
    total_neto: Any,
    impuestos: Any,
    cargos: Any,
    descuentos: Any,
    sum_line_total: Any,
) -> ConsistenciaOrden:
    observed_total = _number(order_total)
    observed_lines = _number(sum_line_total)
    if observed_total is None or observed_lines is None:
        return ConsistenciaOrden("NOT_EVALUABLE", "MISSING_OR_NON_NUMERIC_ORDER_TOTALS", UNKNOWN, observed_total or UNKNOWN, observed_lines or UNKNOWN)
    if abs(observed_lines - observed_total) < 0.01:
        return ConsistenciaOrden("MATCH", "SUM_LINE_TOTAL_MATCHES_ORDER_TOTAL", observed_lines, observed_total, observed_lines)

    net = _number(total_neto)
    tax = _number(impuestos) or 0.0
    charge = _number(cargos) or 0.0
    discount = _number(descuentos) or 0.0
    if net is not None:
        expected_header = net + tax + charge - discount
        if abs(expected_header - observed_total) < 0.01:
            return ConsistenciaOrden(
                "MISMATCH",
                "ORDER_TOTAL_MATCHES_HEADER_NET_TAX_CHARGES_DISCOUNTS_NOT_LINE_TOTALS",
                expected_header,
                observed_total,
                observed_lines,
            )
    return ConsistenciaOrden("MISMATCH", "ORDER_TOTAL_DIFFERS_FROM_SUM_LINE_TOTAL", UNKNOWN, observed_total, observed_lines)


def _code(value: Any) -> str:
    if value in (None, "", [], {}, UNKNOWN):
        return UNKNOWN
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        return str(value).strip()
    return str(numeric)


def _number(value: Any) -> float | None:
    if value in (None, "", [], {}, UNKNOWN):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
