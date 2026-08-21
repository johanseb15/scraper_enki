from types import SimpleNamespace

import pytest

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    ObservationUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.infraestructura import semantic_understanding_composer as composer


def _prov(kind="SEMANTIC_NORMALIZATION", reference="semantic.csv"):
    return KnowledgeProvenance(kind, reference, "v1")


def _observation(
    role: SemanticObservationRole,
    *,
    raw="raw expression",
    canonical_service=None,
    matched_services=(),
):
    return SemanticObservation(
        observation_id="obs-1",
        raw_expression=raw,
        semantic_role=role,
        market_scope="UNKNOWN",
        source="provider_a",
        provider="Provider A",
        province="Córdoba",
        observation_provenance=_prov("COMMERCIAL_OBSERVATION", "row:1"),
        interpretation_provenance=_prov(),
        canonical_service=canonical_service,
        matched_services=matched_services,
    )


def _meaning(status_value: str):
    return SimpleNamespace(
        understanding_status=SimpleNamespace(value=status_value),
    )


@pytest.mark.parametrize(
    ("role", "interpreter_name"),
    [
        (SemanticObservationRole.PRICE_CONTEXT, "interpret_price_context"),
        (SemanticObservationRole.SCOPE_DEVICE, "interpret_scope_meaning"),
        (SemanticObservationRole.HARDWARE_PRODUCT, "interpret_hardware_meaning"),
        (SemanticObservationRole.NON_OBJECT, "interpret_non_object_meaning"),
        (SemanticObservationRole.LOGISTICS_CONTEXT, "interpret_logistics_meaning"),
    ],
)
def test_composer_dispatches_each_typed_role(monkeypatch, role, interpreter_name):
    expected = _meaning("SOMETHING_UNDERSTOOD")
    called = []

    def fake_interpreter(observation):
        called.append(observation)
        return expected

    monkeypatch.setitem(composer._TYPED_INTERPRETERS, role, fake_interpreter)

    obs = _observation(role)
    envelope = composer.compose_semantic_understanding(obs)

    assert called == [obs]
    assert envelope.meaning is expected
    assert envelope.status is ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD


def test_single_service_keeps_fully_represented_status_without_interpreter():
    obs = _observation(
        SemanticObservationRole.SINGLE_SERVICE,
        canonical_service="SOPORTE_REMOTO",
    )

    envelope = composer.compose_semantic_understanding(obs)

    assert envelope.meaning is None
    assert envelope.status is ObservationUnderstandingStatus.FULLY_REPRESENTED


def test_composite_service_keeps_existing_partial_status_without_interpreter():
    obs = _observation(
        SemanticObservationRole.COMPOSITE_SERVICE,
        matched_services=("BACKUP", "FORMATEO"),
    )

    envelope = composer.compose_semantic_understanding(obs)

    assert envelope.meaning is None
    assert envelope.status is ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD


def test_unmapped_stays_unknown_without_interpreter():
    obs = _observation(SemanticObservationRole.UNMAPPED)

    envelope = composer.compose_semantic_understanding(obs)

    assert envelope.meaning is None
    assert envelope.status is ObservationUnderstandingStatus.UNKNOWN


@pytest.mark.parametrize(
    ("typed_status", "expected"),
    [
        ("HARDWARE_AMBIGUOUS", ObservationUnderstandingStatus.AMBIGUOUS),
        ("NON_OBJECT_UNKNOWN", ObservationUnderstandingStatus.UNKNOWN),
        ("SCOPE_PARTIAL", ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD),
        ("LOGISTICS_UNDERSTOOD", ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD),
        ("PRICE_CONTEXT_UNDERSTOOD", ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD),
        ("UNEXPECTED_STATUS", ObservationUnderstandingStatus.UNREPRESENTED),
    ],
)
def test_typed_status_is_normalized_without_hiding_uncertainty(
    monkeypatch,
    typed_status,
    expected,
):
    monkeypatch.setitem(
        composer._TYPED_INTERPRETERS,
        SemanticObservationRole.HARDWARE_PRODUCT,
        lambda _: _meaning(typed_status),
    )

    envelope = composer.compose_semantic_understanding(
        _observation(SemanticObservationRole.HARDWARE_PRODUCT)
    )

    assert envelope.status is expected


def test_envelope_preserves_both_provenance_channels():
    obs = _observation(SemanticObservationRole.UNMAPPED)

    envelope = composer.compose_semantic_understanding(obs)

    assert envelope.observation_provenance == obs.observation_provenance
    assert envelope.interpretation_provenance == obs.interpretation_provenance


def test_composer_has_no_persistence_or_promotion_surface():
    envelope = composer.compose_semantic_understanding(
        _observation(SemanticObservationRole.UNMAPPED)
    )

    assert not hasattr(envelope, "save")
    assert not hasattr(envelope, "promote")
    assert not hasattr(envelope, "persist")


def test_composer_does_not_change_pricing_runtime():
    from src.aplicacion.parser_consulta_pricing import parse_pricing_query

    before = parse_pricing_query("cuánto sale instalar Windows")
    composer.compose_semantic_understanding(
        _observation(SemanticObservationRole.UNMAPPED)
    )
    after = parse_pricing_query("cuánto sale instalar Windows")

    assert after == before
