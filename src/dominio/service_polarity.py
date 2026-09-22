from __future__ import annotations

import re
import unicodedata


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    ).lower()


def explicit_backup_excluded(text: str) -> bool:
    """Return whether the text explicitly excludes backup from the service."""
    x = re.sub(r"\s+", " ", _fold(text)).strip()
    return bool(
        re.search(
            r"\b(?:sin|no\s+incluye|no\s+incluido|no\s+incluida)\s+"
            r"(?:el\s+|la\s+|los\s+|las\s+)?"
            r"(?:back[ -]?up|backup|respaldo|copia de seguridad)\b",
            x,
        )
    )
