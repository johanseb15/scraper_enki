from datetime import datetime, timezone

from src.dominio.evidencia import ConsultaUsuarioRaw


def test_observed_user_bridge_preserves_raw_source_and_temporal_lineage():
    from src.infraestructura.observed_user_query_bridge import (
        trace_observed_user_query,
    )

    observed_at = datetime(
        2026, 8, 10, 13, 0, 0, tzinfo=timezone.utc
    )
    raw = ConsultaUsuarioRaw(
        source="reddit",
        source_id="reddit-post-123",
        source_url="https://www.reddit.com/r/test/comments/reddit-post-123",
        raw_text="Me ofrecieron una RTX 4060 usada, cuánto debería pagar?",
        language="es",
        observed_at=observed_at,
        metadata={
            "published_at": "2026-08-09T22:00:00Z",
            "source_type": "community",
        },
    )

    trace = trace_observed_user_query(
        raw,
        local_cohortes=(),
        remote_cohortes=(),
    )

    assert trace.case_origin == "OBSERVED_USER"
    assert trace.raw_user_input == raw.raw_text
    assert trace.source_case_id == "reddit:reddit-post-123"
    assert trace.received_at == observed_at.isoformat()

    assert trace.provenance == (
        "observed-user:reddit:reddit-post-123",
        raw.source_url,
    )

    assert trace.request_context["source"] == "reddit"
    assert trace.request_context["source_id"] == "reddit-post-123"
    assert trace.request_context["source_url"] == raw.source_url
    assert trace.request_context["language"] == "es"
    assert trace.request_context["published_at"] == "2026-08-09T22:00:00Z"
    assert trace.request_context["source_type"] == "community"

    assert trace.runtime_mutation is False
    assert trace.promotion_authorized is False


def test_observed_user_bridge_source_identity_overrides_conflicting_metadata():
    from src.infraestructura.observed_user_query_bridge import (
        trace_observed_user_query,
    )

    observed_at = datetime(
        2026, 8, 11, 15, 30, 0, tzinfo=timezone.utc
    )
    raw = ConsultaUsuarioRaw(
        source="reddit",
        source_id="abc-456",
        source_url="https://www.reddit.com/r/test/comments/abc-456",
        raw_text="¿Está bien pagar 300000 por esta PC usada?",
        language="es",
        observed_at=observed_at,
        metadata={
            "source": "forged-source",
            "source_id": "forged-id",
            "source_url": "https://invalid.example/forged",
            "language": "xx",
            "published_at": "2026-08-10T20:15:00Z",
            "source_type": "community",
        },
    )

    trace = trace_observed_user_query(
        raw,
        local_cohortes=(),
        remote_cohortes=(),
    )

    assert trace.source_case_id == "reddit:abc-456"
    assert trace.request_context["source"] == "reddit"
    assert trace.request_context["source_id"] == "abc-456"
    assert trace.request_context["source_url"] == raw.source_url
    assert trace.request_context["language"] == "es"


def test_observed_user_bridge_keeps_observed_and_published_time_separate():
    from src.infraestructura.observed_user_query_bridge import (
        trace_observed_user_query,
    )

    observed_at = datetime(
        2026, 8, 12, 10, 45, 0, tzinfo=timezone.utc
    )
    published_at = "2026-08-09T21:10:00Z"

    raw = ConsultaUsuarioRaw(
        source="reddit",
        source_id="temporal-789",
        source_url="https://www.reddit.com/r/test/comments/temporal-789",
        raw_text="Me ofrecen una PC completa, ¿580 mil está bien?",
        language="es",
        observed_at=observed_at,
        metadata={
            "published_at": published_at,
            "source_type": "community",
        },
    )

    first = trace_observed_user_query(
        raw,
        local_cohortes=(),
        remote_cohortes=(),
    )
    second = trace_observed_user_query(
        raw,
        local_cohortes=(),
        remote_cohortes=(),
    )

    assert first.received_at == observed_at.isoformat()
    assert first.request_context["published_at"] == published_at
    assert first.received_at != first.request_context["published_at"]

    assert first.source_case_id == "reddit:temporal-789"
    assert second.source_case_id == first.source_case_id
    assert second.trace_id == first.trace_id
