from __future__ import annotations

import re
from datetime import date


_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


_EFFECTIVE_FROM_PATTERN = re.compile(
    r"\ba\s+partir\s+del"
    r"(?:\s+d[ií]a)?"
    r"(?:\s+[a-záéíóúñ]+)?"
    r"\s+(\d{1,2})"
    r"\s+de\s+"
    r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
    r"septiembre|octubre|noviembre|diciembre)"
    r"\s+(?:de|del)\s+"
    r"(20\d{2}|2\.\d{3})\b",
    re.IGNORECASE,
)


_NEXT_UPDATE_PATTERN = re.compile(
    r"\bsiendo\s+la\s+pr[oó]xima\s+el\s+"
    r"(\d{1,2})"
    r"\s+de\s+"
    r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
    r"septiembre|octubre|noviembre|diciembre)"
    r"\s+(?:de|del)\s+"
    r"(20\d{2}|2\.\d{3})\b",
    re.IGNORECASE,
)


def _date_from_match(match: re.Match[str] | None) -> str | None:
    if match is None:
        return None

    day_raw, month_raw, year_raw = match.groups()

    day = int(day_raw)
    month = _MONTHS[month_raw.casefold()]
    year = int(year_raw.replace(".", ""))

    try:
        value = date(year, month, day)
    except ValueError:
        return None

    return value.isoformat()


def extract_explicit_valid_from(text: str) -> str | None:
    """Return a source-declared day-level effective-from date.

    Bare month/year context is intentionally insufficient.
    """

    return _date_from_match(
        _EFFECTIVE_FROM_PATTERN.search(text)
    )


def extract_explicit_next_update(text: str) -> str | None:
    """Return the source-declared next scheduled update date.

    This is scheduling evidence only. It is not valid_to and does not prove
    CURRENT pricing.
    """

    return _date_from_match(
        _NEXT_UPDATE_PATTERN.search(text)
    )
