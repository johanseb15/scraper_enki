from __future__ import annotations

import importlib


def test_explicit_effective_from_requires_day_level_source_language():
    """
    Preserve only a source-declared day-level effective-from date.

    A bare month/year label remains price-time context and must not be
    upgraded into an effective validity boundary.
    """

    module = importlib.import_module(
        "src.infraestructura.explicit_temporal_validity_extractor"
    )

    extract_valid_from = getattr(
        module,
        "extract_explicit_valid_from",
    )

    cpitlp_basis = (
        "Se informa que a partir del Martes 1 de Septiembre del 2026 "
        "el metro cuadrado de construcción que se utiliza para el cálculo "
        "del honorario y del aporte para tareas profesionales se actualizará "
        "a $1.900.000."
    )

    assert extract_valid_from(cpitlp_basis) == "2026-09-01"

    # Existing month/year price-time evidence is weaker: it must NOT be
    # silently converted into a day-level effective validity boundary.
    assert (
        extract_valid_from(
            "Lista de precios. Precios orientativos — septiembre 2026."
        )
        is None
    )
