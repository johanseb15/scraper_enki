from __future__ import annotations

from src.dominio.evidencia import ConsultaUsuarioRaw
from src.infraestructura.real_world_query_tracer import trace_real_world_query


def trace_observed_user_query(
    raw: ConsultaUsuarioRaw,
    *,
    local_cohortes,
    remote_cohortes,
):
    source_case_id = f"{raw.source}:{raw.source_id}"

    request_context = dict(raw.metadata)
    request_context.update(
        {
            "source": raw.source,
            "source_id": raw.source_id,
            "source_url": raw.source_url,
            "language": raw.language,
        }
    )

    return trace_real_world_query(
        raw.raw_text,
        local_cohortes=local_cohortes,
        remote_cohortes=remote_cohortes,
        source_case_id=source_case_id,
        case_origin="OBSERVED_USER",
        provenance=(
            f"observed-user:{source_case_id}",
            raw.source_url,
        ),
        received_at=raw.observed_at.isoformat(),
        request_context=request_context,
    )
