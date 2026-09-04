from __future__ import annotations

from src.infraestructura.explicit_temporal_validity_extractor import (
    extract_explicit_valid_from,
)


def test_explicit_effective_from_accepts_primary_resolution_language():
    """
    Preserve the day-level effective-from date exactly as declared by the
    primary CPITLP resolution.

    The dotted year spelling is source text, not a reason to discard the
    otherwise explicit validity boundary.
    """

    source_basis = (
        "cálculo de los honorarios y aportes profesionales "
        "con vigencia a partir del día 01 de septiembre de 2.026."
    )

    assert extract_explicit_valid_from(source_basis) == "2026-09-01"
