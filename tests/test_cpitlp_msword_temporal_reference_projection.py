from __future__ import annotations

import importlib


def test_cpitlp_msword_primary_reference_projects_exact_valid_from():
    """
    Compose the source-specific legacy Word text projection with the CPITLP
    temporal applicability rule.

    The same primary document may yield valid_from only for an exact
    object/price pair present under the Informatics reference-table scope.
    """

    module = importlib.import_module(
        "src.infraestructura.cpitlp_temporal_reference_extractor"
    )

    extract_from_msword = getattr(
        module,
        "extract_valid_from_from_msword_reference",
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

    assert (
        extract_from_msword(
            raw_bytes,
            economic_object_raw="TÉCNICO HARDWARE/SOFTWARE ($/hora)",
            price_raw="$ 33.193",
        )
        == "2026-09-01"
    )

    # Same document, wrong price: applicability must fail closed.
    assert (
        extract_from_msword(
            raw_bytes,
            economic_object_raw="TÉCNICO HARDWARE/SOFTWARE ($/hora)",
            price_raw="$ 47.120",
        )
        is None
    )

    # Non-OLE input is not admissible as a CPITLP legacy Word source.
    assert (
        extract_from_msword(
            b"<html>not the primary Word document</html>",
            economic_object_raw="TÉCNICO HARDWARE/SOFTWARE ($/hora)",
            price_raw="$ 33.193",
        )
        is None
    )
