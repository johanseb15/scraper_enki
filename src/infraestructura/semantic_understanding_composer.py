from __future__ import annotations

from collections.abc import Callable

from src.dominio.semantic_observation import (
    ObservationUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.dominio.semantic_understanding import SemanticUnderstandingEnvelope
from src.infraestructura.hardware_meaning_interpreter import (
    interpret_hardware_meaning,
)
from src.infraestructura.logistics_meaning_interpreter import (
    interpret_logistics_meaning,
)
from src.infraestructura.non_object_meaning_interpreter import (
    interpret_non_object_meaning,
)
from src.infraestructura.price_context_interpreter import interpret_price_context
from src.infraestructura.scope_meaning_interpreter import interpret_scope_meaning


TypedInterpreter = Callable[[SemanticObservation], object]


_TYPED_INTERPRETERS: dict[SemanticObservationRole, TypedInterpreter] = {
    SemanticObservationRole.PRICE_CONTEXT: interpret_price_context,
    SemanticObservationRole.SCOPE_DEVICE: interpret_scope_meaning,
    SemanticObservationRole.HARDWARE_PRODUCT: interpret_hardware_meaning,
    SemanticObservationRole.NON_OBJECT: interpret_non_object_meaning,
    SemanticObservationRole.LOGISTICS_CONTEXT: interpret_logistics_meaning,
}


def compose_semantic_understanding(
    observation: SemanticObservation,
) -> SemanticUnderstandingEnvelope:
    interpreter = _TYPED_INTERPRETERS.get(observation.semantic_role)

    if interpreter is None:
        return SemanticUnderstandingEnvelope(
            observation=observation,
            status=observation.understanding_status,
            meaning=None,
        )

    meaning = interpreter(observation)
    return SemanticUnderstandingEnvelope(
        observation=observation,
        status=_observation_level_status(meaning),
        meaning=meaning,
    )


def _observation_level_status(meaning: object) -> ObservationUnderstandingStatus:
    typed_status = getattr(meaning, "understanding_status", None)
    raw_status = getattr(typed_status, "value", str(typed_status or "")).upper()

    if "AMBIGUOUS" in raw_status:
        return ObservationUnderstandingStatus.AMBIGUOUS
    if "UNKNOWN" in raw_status:
        return ObservationUnderstandingStatus.UNKNOWN

    # A typed context meaning increases semantic understanding, but it does not
    # make the whole commercial observation fully represented by itself.
    if "UNDERSTOOD" in raw_status or "PARTIAL" in raw_status:
        return ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD

    return ObservationUnderstandingStatus.UNREPRESENTED
