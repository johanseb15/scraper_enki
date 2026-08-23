from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path

from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing_runtime
from src.dominio.real_world_query_trace import InputModality
from src.infraestructura.real_world_query_tracer import append_trace, trace_real_world_query


def main():
    parser = ArgumentParser(description="Append one human real query trace through Enki's real runtime.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--case-id", required=True, help="Non-secret stable field-case identifier.")
    parser.add_argument("--out", default="data/field/real_world_query_traces_v1.jsonl")
    args = parser.parse_args()
    local, remote = cargar_cohortes_pricing_runtime()
    trace = trace_real_world_query(
        args.query, local_cohortes=local, remote_cohortes=remote,
        source_case_id=args.case_id, case_origin="HUMAN_REAL", input_modality=InputModality.TEXT,
        provenance=("founder-field-intake",), received_at=datetime.now(timezone.utc).isoformat(),
    )
    append_trace(Path(args.out), trace)
    print(f"TRACE_ID={trace.trace_id}")
    print(f"READINESS={trace.readiness}")
    print(f"FAILURES={','.join(item.value for item in trace.failures)}")
    print(f"PROMOTION_AUTHORIZED={trace.promotion_authorized}")


if __name__ == "__main__":
    main()
