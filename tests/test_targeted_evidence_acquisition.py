import hashlib
import json
from datetime import datetime, timezone

import requests

from src.infraestructura.targeted_evidence_acquisition import acquire_planned_sources


class Response:
    def __init__(self, content=b"<html>new</html>", status=200):
        self.content = content; self.status_code = status
        self.headers = {"Content-Type": "text/html", "ETag": "v1"}
    def raise_for_status(self):
        if self.status_code >= 400: raise requests.HTTPError(str(self.status_code))


class Session:
    def __init__(self, responses): self.responses = iter(responses); self.calls = []
    def get(self, url, **kwargs): self.calls.append((url, kwargs)); return next(self.responses)


def write_plan(path, actions):
    path.write_text("".join(json.dumps(item) + "\n" for item in actions), encoding="utf-8")


def test_requests_are_deduplicated_and_changed_raw_is_versioned(tmp_path):
    old = tmp_path / "old.html"; old.write_bytes(b"<html>old</html>")
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(f"source,raw_path,source_url,acquired_at\ns,{old},https://x.test,\n", encoding="utf-8")
    plan = tmp_path / "plan.jsonl"
    action = {"source": "s", "source_url": "https://x.test"}
    write_plan(plan, [action, action])
    session = Session([Response()])
    output = tmp_path / "acq.jsonl"
    metrics = acquire_planned_sources(plan, manifest, tmp_path / "raw", output, session=session, now=lambda: datetime(2026, 8, 22, tzinfo=timezone.utc))
    assert len(session.calls) == 1
    assert metrics["NETWORK_REQUESTS"] == 1
    assert metrics["CHANGED_CONTENT"] == 1
    row = json.loads(output.read_text(encoding="utf-8"))
    assert row["content_hash"] == hashlib.sha256(b"<html>new</html>").hexdigest()
    assert __import__("pathlib").Path(row["raw_document_reference"]).exists()


def test_unchanged_and_blocked_are_explicit_without_bypass(tmp_path):
    raw = tmp_path / "old.html"; raw.write_bytes(b"same")
    manifest = tmp_path / "manifest.csv"; manifest.write_text(f"source,raw_path,source_url,acquired_at\na,{raw},https://a,\n", encoding="utf-8")
    plan = tmp_path / "plan.jsonl"; write_plan(plan, [{"source":"a","source_url":"https://a"},{"source":"b","source_url":"https://b"}])
    session = Session([Response(b"same"), Response(status=403)])
    metrics = acquire_planned_sources(plan, manifest, tmp_path / "raw", tmp_path / "out.jsonl", session=session)
    assert metrics["UNCHANGED_CONTENT"] == 1
    assert metrics["BLOCKED"] == 1
    assert len(session.calls) == 2
    assert raw.read_bytes() == b"same"
    assert all(call[1]["timeout"] == 15 for call in session.calls)
    assert all("verify" not in call[1] for call in session.calls)


def test_failed_request_preserves_historical_raw(tmp_path):
    raw = tmp_path / "historical.html"; raw.write_bytes(b"historical evidence")
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(f"source,raw_path,source_url,acquired_at\ns,{raw},https://s.test,\n", encoding="utf-8")
    plan = tmp_path / "plan.jsonl"; write_plan(plan, [{"source": "s", "source_url": "https://s.test"}])

    class FailedSession:
        def get(self, url, **kwargs):
            raise requests.Timeout("timeout")

    output = tmp_path / "out.jsonl"
    metrics = acquire_planned_sources(plan, manifest, tmp_path / "new", output, session=FailedSession())
    row = json.loads(output.read_text(encoding="utf-8"))
    assert metrics["SOURCES_FAILED"] == 1
    assert row["status"] == "UNAVAILABLE"
    assert row["raw_document_reference"] is None
    assert raw.read_bytes() == b"historical evidence"
