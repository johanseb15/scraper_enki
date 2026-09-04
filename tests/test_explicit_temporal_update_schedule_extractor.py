from __future__ import annotations

import importlib


def test_explicit_next_update_is_preserved_as_schedule_evidence():
    """
    Preserve the source-declared next scheduled update as its own signal.

    This is scheduling evidence only. It must not be interpreted here as
    valid_to or as proof of CURRENT pricing.
    """

    module = importlib.import_module(
        "src.infraestructura.explicit_temporal_validity_extractor"
    )

    extract_next_update = getattr(
        module,
        "extract_explicit_next_update",
    )

    source_basis = (
        "Recordamos, también, que estos valores se volverán a actualizar "
        "dentro de 3 meses, siendo la próxima el 1 de Diciembre de 2026."
    )

    assert extract_next_update(source_basis) == "2026-12-01"
