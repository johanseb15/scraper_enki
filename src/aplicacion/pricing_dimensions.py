from __future__ import annotations

import re
import unicodedata


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


def infer_price_scope(economic_object_raw: str) -> str:
    """Return cadence only when it is explicit in preserved source text."""
    text = _fold(economic_object_raw)
    if re.search(
        r"\bx\s*1\s*(?:hs?|hora)\b|\bpor\s+hora\b|\bla\s+hora\b"
        r"|\bhora\s+(?:inicial|adicional|servicio|tecnica|tecnico)\b"
        r"|\bhora(?:s)?\s+de\s+(?:servicio|soporte|trabajo)\b",
        text,
    ):
        return "PER_HOUR"
    if re.search(
        r"\bpor\s+mes\b|\bal\s+mes\b|\bmensual(?:mente)?\b|\babono\s+mensual\b",
        text,
    ):
        return "PER_MONTH"
    if re.search(r"\bpor\s+visita\b|\bcada\s+visita\b", text):
        return "PER_VISIT"
    if re.search(
        r"\bpor\s+(?:equipo|unidad|pc|notebook|camara)\b"
        r"|\bcada\s+\d+(?:[.,]\d+)?\s*(?:gb|tb)\b",
        text,
    ):
        return "PER_UNIT"
    return "UNKNOWN"


def infer_commercial_context(economic_object_raw: str) -> str:
    text = _fold(economic_object_raw)
    if re.search(
        r"\burgenc(?:ia|ias)\b|\bfuera\s+de\s+horario\b"
        r"|\bfin(?:es)?\s+de\s+semana\b|\bferiado(?:s)?\b",
        text,
    ):
        return "URGENCY"
    return "STANDARD"
