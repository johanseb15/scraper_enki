import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_trace_real_query_runs_from_repo_root_without_pythonpath(tmp_path):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    traces = tmp_path / "traces.jsonl"
    cases = tmp_path / "cases.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/trace_real_query.py",
            "--case-id",
            "e2e-entrypoint-probe",
            "--query",
            "Cuánto puedo cobrar por formatear una notebook?",
            "--out",
            str(traces),
            "--cases-out",
            str(cases),
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert "READINESS=CLARIFICATION_REQUIRED" in completed.stdout
    case_rows = [json.loads(line) for line in cases.read_text(encoding="utf-8").splitlines()]
    trace_rows = [json.loads(line) for line in traces.read_text(encoding="utf-8").splitlines()]
    assert len(case_rows) == len(trace_rows) == 1
    assert case_rows[0]["source_type"] == "HUMAN_REAL"
    assert trace_rows[0]["case_origin"] == "HUMAN_REAL"
