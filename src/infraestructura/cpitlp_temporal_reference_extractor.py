from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

from src.infraestructura.cpitlp_msword_text_extractor import (
    extract_cpitlp_msword_text,
)
from src.infraestructura.explicit_temporal_validity_extractor import (
    extract_explicit_valid_from,
)


_PRICE_TOKEN_PATTERN = re.compile(
    r"(?:\$|ars)\s*\d(?:[\d.,]*\d)?",
    re.IGNORECASE,
)

_EXTRACTOR_VERSION = (
    "cpitlp-explicit-temporal-reference-v1"
)


@dataclass(frozen=True)
class CPITLPTemporalReferenceClaim:
    source_id: str
    source_url: str | None
    acquired_at: str | None
    raw_document_id: str
    economic_object_raw: str
    price_raw: str
    valid_from: str
    valid_to: str | None
    raw_basis: str
    extractor_version: str
    provenance: tuple[str, ...]


def _fold(value: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value or "",
    )

    return " ".join(
        "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )
        .casefold()
        .split()
    )


def _compact_price(value: str) -> str:
    return "".join(
        character
        for character in _fold(value)
        if not character.isspace()
    )


def _has_informatics_reference_scope(
    raw_basis: str,
) -> bool:
    folded = _fold(raw_basis)

    return (
        "honorarios de referencia" in folded
        and "ciencias informaticas" in folded
    )


def _object_is_paired_with_price(
    raw_basis: str,
    *,
    economic_object_raw: str,
    price_raw: str,
) -> bool:
    """Require the first local price after an exact object occurrence."""

    folded_basis = _fold(raw_basis)
    target = _fold(economic_object_raw)
    expected_price = _compact_price(
        price_raw
    )

    if not target or not expected_price:
        return False

    search_from = 0

    while True:
        object_index = folded_basis.find(
            target,
            search_from,
        )

        if object_index < 0:
            return False

        local_start = (
            object_index
            + len(target)
        )

        local_suffix = folded_basis[
            local_start:local_start + 120
        ]

        price_match = _PRICE_TOKEN_PATTERN.search(
            local_suffix
        )

        if (
            price_match is not None
            and _compact_price(
                price_match.group(0)
            )
            == expected_price
        ):
            return True

        search_from = object_index + 1


def extract_valid_from_for_reference(
    raw_basis: str,
    *,
    economic_object_raw: str,
    price_raw: str,
) -> str | None:
    """Bind CPITLP validity only to an explicit Informatics table row."""

    if not _has_informatics_reference_scope(
        raw_basis
    ):
        return None

    if not _object_is_paired_with_price(
        raw_basis,
        economic_object_raw=(
            economic_object_raw
        ),
        price_raw=price_raw,
    ):
        return None

    return extract_explicit_valid_from(
        raw_basis
    )


def extract_valid_from_from_msword_reference(
    raw_bytes: bytes,
    *,
    economic_object_raw: str,
    price_raw: str,
) -> str | None:
    """Project CPITLP legacy Word RAW to an exact reference valid_from."""

    raw_basis = extract_cpitlp_msword_text(
        raw_bytes
    )

    if raw_basis is None:
        return None

    return extract_valid_from_for_reference(
        raw_basis,
        economic_object_raw=(
            economic_object_raw
        ),
        price_raw=price_raw,
    )


def build_cpitlp_temporal_reference_claim(
    raw_bytes: bytes,
    *,
    source_id: str,
    source_url: str | None,
    acquired_at: str | None,
    content_hash: str,
    economic_object_raw: str,
    price_raw: str,
) -> CPITLPTemporalReferenceClaim | None:
    """Build an immutable explicit-validity claim with exact RAW lineage."""

    digest = hashlib.sha256(
        raw_bytes
    ).hexdigest()

    if digest != content_hash:
        return None

    raw_basis = extract_cpitlp_msword_text(
        raw_bytes
    )

    if raw_basis is None:
        return None

    valid_from = (
        extract_valid_from_for_reference(
            raw_basis,
            economic_object_raw=(
                economic_object_raw
            ),
            price_raw=price_raw,
        )
    )

    if valid_from is None:
        return None

    raw_document_id = f"sha256:{digest}"

    return CPITLPTemporalReferenceClaim(
        source_id=source_id,
        source_url=source_url,
        acquired_at=acquired_at,
        raw_document_id=raw_document_id,
        economic_object_raw=(
            economic_object_raw
        ),
        price_raw=price_raw,
        valid_from=valid_from,
        valid_to=None,
        raw_basis=raw_basis,
        extractor_version=(
            _EXTRACTOR_VERSION
        ),
        provenance=(
            raw_document_id,
        ),
    )
