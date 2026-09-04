from __future__ import annotations

import importlib


def test_cpitlp_primary_resolution_valid_from_applies_only_with_explicit_scope():
    """
    A CPITLP primary resolution can bind an explicit effective-from date to the
    exact Informatics reference row when the resolution itself declares the
    Informatics table scope.

    A news page where the effective date is attached to an unrelated
    construction value must not fan that date out to the technical reference.
    """

    module = importlib.import_module(
        "src.infraestructura.cpitlp_temporal_reference_extractor"
    )

    extract_valid_from_for_reference = getattr(
        module,
        "extract_valid_from_for_reference",
    )

    primary_resolution_basis = (
        "RESOLUCION N 11. "
        "Aprobar la actualizacion de la Tabla Honorarios de Referencia - "
        "Ciencias Informaticas, para el calculo de los honorarios y aportes "
        "profesionales con vigencia a partir del dia 01 de septiembre de "
        "2.026. ANEXO I. TECNICO HARDWARE/SOFTWARE ($/hora) $ 33.193."
    )

    assert (
        extract_valid_from_for_reference(
            primary_resolution_basis,
            economic_object_raw="TECNICO HARDWARE/SOFTWARE ($/hora)",
            price_raw="$ 33.193",
        )
        == "2026-09-01"
    )

    news_page_basis = (
        "Se informa que a partir del Martes 1 de Septiembre del 2026 "
        "el metro cuadrado de construccion se actualizara a $1.900.000. "
        "El aporte minimo al Consejo se actualizara a $18.000. "
        "El valor de referencia de Tecnico Hardware/Software en los "
        "honorarios informaticos se actualizara a $33.193."
    )

    assert (
        extract_valid_from_for_reference(
            news_page_basis,
            economic_object_raw="Tecnico Hardware/Software",
            price_raw="$33.193",
        )
        is None
    )
