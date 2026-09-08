"""CPITLP primary reference prices, without temporal or commercial admission."""

import hashlib
import re

from src.dominio.evidencia import RegistroPrecioReferenciaObservado
from src.infraestructura.cpitlp_msword_text_extractor import extract_cpitlp_msword_text
from src.infraestructura.cpitlp_temporal_reference_extractor import (
    _has_informatics_reference_scope,
    _object_is_paired_with_price,
)

_TARGET = "TÉCNICO HARDWARE/SOFTWARE ($/hora)"
_PRICE = re.compile(r"\$\s*([0-9]{1,3}(?:\.[0-9]{3})*)")


def build_cpitlp_reference_price_observation(
    raw_bytes: bytes,
    *,
    source_id: str,
    source_url: str | None,
    content_hash: str,
    economic_object_raw: str,
    price_raw: str,
) -> RegistroPrecioReferenciaObservado | None:
    """Verify a requested exact CPITLP row against its primary RAW bytes."""
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != content_hash or economic_object_raw != _TARGET:
        return None
    raw_basis = extract_cpitlp_msword_text(raw_bytes)
    if raw_basis is None or not _has_informatics_reference_scope(raw_basis):
        return None
    if not _object_is_paired_with_price(
        raw_basis, economic_object_raw=economic_object_raw, price_raw=price_raw
    ):
        return None
    # Word table cells use BEL; never cross intervening row text.
    adjacent = re.search(
        re.escape(economic_object_raw)
        + r"[\s\x07]*(" + _PRICE.pattern + r")(?![0-9.,])",
        raw_basis,
    )
    if adjacent is None or re.sub(r"\s+", "", adjacent.group(1)) != re.sub(
        r"\s+", "", price_raw
    ):
        return None
    match = _PRICE.fullmatch(price_raw)
    if match is None:
        return None
    return RegistroPrecioReferenciaObservado(
        raw_document_identity=f"sha256:{digest}",
        source="CPITLP",
        source_id=source_id,
        source_url=source_url,
        extractor_version="cpitlp-reference-price-v1",
        economic_object_raw=economic_object_raw,
        price_raw=price_raw,
        price_value=int(match.group(1).replace(".", "")),
        currency_raw="ARS",
        unit_raw="PER_HOUR",
    )
