from src.dominio.semantic_observation import ObservationUnderstandingStatus
from src.infraestructura.semantic_understanding_batch import (
    compose_semantic_understanding_rows,
)


def _row(
    observation_id,
    raw_expression,
    semantic_role,
    *,
    canonical_service="",
    matched_services="",
):
    return {
        "observation_id": observation_id,
        "economic_object_raw": raw_expression,
        "semantic_role": semantic_role,
        "market_scope": "UNKNOWN",
        "source": "provider_a",
        "provider": "Provider A",
        "province": "Córdoba",
        "canonical_service": canonical_service,
        "matched_services": matched_services,
    }


def test_batch_connects_adapter_and_composer_for_mixed_rows():
    rows = [
        _row("1", "instalación de Windows", "SINGLE_SERVICE", canonical_service="INSTALACION_SO"),
        _row("2", "Desde", "NON_OBJECT"),
        _row("3", "DISPONIBLE", "NON_OBJECT"),
        _row("4", "*", "NON_OBJECT"),
    ]

    envelopes = compose_semantic_understanding_rows(
        rows,
        interpretation_reference="semantic.csv",
        interpretation_version="v1",
    )

    assert len(envelopes) == 4
    assert envelopes[0].status is ObservationUnderstandingStatus.FULLY_REPRESENTED
    assert envelopes[0].meaning is None
    assert envelopes[1].status is ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD
    assert envelopes[2].status is ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD
    assert envelopes[3].status is ObservationUnderstandingStatus.UNKNOWN


def test_batch_preserves_input_order():
    rows = [
        _row("a", "Precio:", "NON_OBJECT"),
        _row("b", "Desde", "NON_OBJECT"),
        _row("c", "DISPONIBLE", "NON_OBJECT"),
    ]

    envelopes = compose_semantic_understanding_rows(rows)

    assert [e.observation.observation_id for e in envelopes] == ["a", "b", "c"]


def test_batch_preserves_provenance_separation():
    rows = [_row("1", "Desde", "NON_OBJECT")]

    envelope = compose_semantic_understanding_rows(
        rows,
        interpretation_reference="artifact/semantic_normalization.csv",
        interpretation_version="v1",
    )[0]

    assert envelope.observation_provenance is not None
    assert envelope.interpretation_provenance is not None
    assert envelope.observation_provenance != envelope.interpretation_provenance


def test_batch_is_read_only_contract():
    envelopes = compose_semantic_understanding_rows(
        [_row("1", "Desde", "NON_OBJECT")]
    )

    envelope = envelopes[0]
    assert not hasattr(envelope, "save")
    assert not hasattr(envelope, "persist")
    assert not hasattr(envelope, "promote")


def test_batch_handles_empty_input():
    assert compose_semantic_understanding_rows([]) == ()
