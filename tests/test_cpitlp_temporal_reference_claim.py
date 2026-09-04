from __future__ import annotations

import hashlib
import importlib


def test_cpitlp_primary_resolution_builds_lineaged_temporal_reference_claim():
    """
    Preserve explicit source-declared effective-from evidence as an immutable
    primary-reference claim with exact RAW lineage.

    This claim is evidence only: it must not invent valid_to, freshness or
    CURRENT semantics.
    """

    module = importlib.import_module(
        "src.infraestructura.cpitlp_temporal_reference_extractor"
    )

    build_claim = getattr(
        module,
        "build_cpitlp_temporal_reference_claim",
    )

    source_text = (
        "ARTICULO 1°: Aprobar la actualización de la Tabla "
        "“Honorarios de Referencia – Ciencias Informáticas” del ANEXO 1, "
        "para el cálculo de los honorarios y aportes profesionales "
        "con vigencia a partir del día 01 de septiembre de 2.026. "
        "ANEXO 1 – “Honorarios de Referencia – Ciencias Informáticas” "
        "Referencia: TÉCNICO HARDWARE/SOFTWARE ($/hora)$ 33.193 "
        "Responsable de Servicio Técnico $ 47.120"
    )

    raw_bytes = (
        bytes.fromhex("d0cf11e0a1b11ae1")
        + source_text.encode("utf-16le")
    )

    digest = hashlib.sha256(
        raw_bytes
    ).hexdigest()

    claim = build_claim(
        raw_bytes,
        source_id="cpitlp_it_resolution_2026_09",
        source_url=(
            "https://noticias.cpitlp.org.ar/"
            "resolution-11-26.doc"
        ),
        acquired_at="2026-09-04T19:16:53.530163+00:00",
        content_hash=digest,
        economic_object_raw="TÉCNICO HARDWARE/SOFTWARE ($/hora)",
        price_raw="$ 33.193",
    )

    assert claim is not None
    assert claim.source_id == "cpitlp_it_resolution_2026_09"
    assert claim.raw_document_id == f"sha256:{digest}"
    assert claim.economic_object_raw == (
        "TÉCNICO HARDWARE/SOFTWARE ($/hora)"
    )
    assert claim.price_raw == "$ 33.193"
    assert claim.valid_from == "2026-09-01"
    assert claim.valid_to is None
    assert claim.acquired_at == (
        "2026-09-04T19:16:53.530163+00:00"
    )
    assert claim.extractor_version == (
        "cpitlp-explicit-temporal-reference-v1"
    )
    assert "vigencia a partir del día" in claim.raw_basis
    assert claim.provenance == (
        f"sha256:{digest}",
    )

    # Exact RAW identity is mandatory. A metadata hash mismatch must not
    # produce a temporal claim from otherwise parseable bytes.
    assert (
        build_claim(
            raw_bytes,
            source_id="cpitlp_it_resolution_2026_09",
            source_url=None,
            acquired_at=None,
            content_hash="0" * 64,
            economic_object_raw="TÉCNICO HARDWARE/SOFTWARE ($/hora)",
            price_raw="$ 33.193",
        )
        is None
    )
