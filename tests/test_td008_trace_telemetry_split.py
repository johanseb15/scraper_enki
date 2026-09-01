from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.infraestructura.real_world_query_tracer import (
    semantic_trace_payload,
    trace_real_world_query,
    trace_telemetry_payload,
)
from src.infraestructura.real_world_trace_artifact import build_real_world_trace_artifacts


ROOT = Path(__file__).resolve().parents[1]


def run():
    return trace_real_world_query(
        "Cuánto puedo cobrar por formatear una notebook?",
        local_cohortes=(),
        remote_cohortes=(),
        source_case_id="td008:trace-split",
        case_origin="CURATED_ENKI",
    )


def _canonical(payload):
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def test_semantic_trace_is_byte_deterministic_while_telemetry_is_separate():
    first = run()
    second = run()
    first_semantic = semantic_trace_payload(first)
    second_semantic = semantic_trace_payload(second)

    assert first.trace_id == second.trace_id
    assert first.replay_fingerprint == second.replay_fingerprint
    assert _canonical(first_semantic) == _canonical(second_semantic)
    assert "total_latency_ms" not in first_semantic
    assert "trace_overhead_ms" not in first_semantic
    assert all("elapsed_ms" not in stage for stage in first_semantic["stages"])

    telemetry = trace_telemetry_payload(first)
    assert telemetry["schema_version"] == "real-world-query-trace-telemetry-v1"
    assert telemetry["trace_id"] == first.trace_id
    assert telemetry["replay_fingerprint"] == first.replay_fingerprint
    assert telemetry["total_latency_ms"] >= 0
    assert telemetry["trace_overhead_ms"] >= 0
    assert len(telemetry["stages"]) == 10
    assert all(stage["elapsed_ms"] >= 0 for stage in telemetry["stages"])


def test_real_world_artifact_build_separates_deterministic_trace_and_telemetry(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_metrics = build_real_world_trace_artifacts(ROOT, first)
    second_metrics = build_real_world_trace_artifacts(ROOT, second)

    first_trace = first / "real_world_query_traces_v2.jsonl"
    second_trace = second / "real_world_query_traces_v2.jsonl"
    first_telemetry = first / "real_world_query_trace_telemetry_v1.jsonl"
    second_telemetry = second / "real_world_query_trace_telemetry_v1.jsonl"

    assert first_trace.read_bytes() == second_trace.read_bytes()
    assert hashlib.sha256(first_trace.read_bytes()).digest() == hashlib.sha256(second_trace.read_bytes()).digest()

    traces = [json.loads(line) for line in first_trace.read_text(encoding="utf-8").splitlines()]
    telemetry = [json.loads(line) for line in first_telemetry.read_text(encoding="utf-8").splitlines()]

    assert len(traces) == len(telemetry) == 50
    assert all(item["schema_version"] == "real-world-query-trace-semantic-v2" for item in traces)
    assert all("total_latency_ms" not in item for item in traces)
    assert all("trace_overhead_ms" not in item for item in traces)
    assert all("elapsed_ms" not in stage for item in traces for stage in item["stages"])
    assert all(item["schema_version"] == "real-world-query-trace-telemetry-v1" for item in telemetry)
    assert first_metrics["TOTAL_TRACES"] == second_metrics["TOTAL_TRACES"] == 50
    assert (first / "real_world_performance_summary_v1.json").exists()
    assert first_telemetry.exists() and second_telemetry.exists()
