from __future__ import annotations

import importlib


def test_cpitlp_legacy_msword_text_is_extracted_from_utf16le_stream():
    """
    CPITLP legacy .doc evidence is admissible only after a deterministic
    source-specific byte-to-text projection.

    The projection must preserve the exact semantic markers required by the
    downstream CPITLP temporal applicability rule.
    """

    module = importlib.import_module(
        "src.infraestructura.cpitlp_msword_text_extractor"
    )

    extract_text = getattr(
        module,
        "extract_cpitlp_msword_text",
    )

    source_text = (
        "ARTICULO 1°: Aprobar la actualización de la Tabla "
        "“Honorarios de Referencia – Ciencias Informáticas” del ANEXO 1, "
        "para el cálculo de los honorarios y aportes profesionales "
        "con vigencia a partir del día 01 de septiembre de 2.026. "
        "ANEXO 1 – “Honorarios de Referencia – Ciencias Informáticas” "
        "Referencia: TÉCNICO HARDWARE/SOFTWARE ($/hora)$ 33.193"
    )

    # OLE Compound File magic followed by the contiguous UTF-16LE text shape
    # observed in the real CPITLP 2026/09 resolution.
    raw_bytes = (
        bytes.fromhex("d0cf11e0a1b11ae1")
        + source_text.encode("utf-16le")
    )

    extracted = extract_text(raw_bytes)

    assert (
        "Honorarios de Referencia – Ciencias Informáticas"
        in extracted
    )
    assert (
        "con vigencia a partir del día 01 de septiembre de 2.026"
        in extracted
    )
    assert (
        "TÉCNICO HARDWARE/SOFTWARE ($/hora)$ 33.193"
        in extracted
    )


def test_cpitlp_msword_text_extractor_rejects_non_ole_bytes():
    module = importlib.import_module(
        "src.infraestructura.cpitlp_msword_text_extractor"
    )

    extract_text = getattr(
        module,
        "extract_cpitlp_msword_text",
    )

    assert extract_text(
        b"<html><body>not a Word OLE document</body></html>"
    ) is None
