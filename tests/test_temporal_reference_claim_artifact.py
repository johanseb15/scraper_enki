from __future__ import annotations

import hashlib
import importlib
import json


def test_explicit_temporal_reference_claim_roundtrips_without_currentness(tmp_path):
    """
    Persist explicit primary-reference validity evidence independently from
    commercial-observation TemporalEvidence.

    The sidecar preserves its own RAW lineage and explicit validity boundary,
    but must not manufacture CURRENT/freshness semantics.
    """

    extractor = importlib.import_module(
        "src.infraestructura.cpitlp_temporal_reference_extractor"
    )
    artifact = importlib.import_module(
        "src.infraestructura.temporal_reference_claim_artifact"
    )

    build_claim = getattr(
        extractor,
        "build_cpitlp_temporal_reference_claim",
    )
    write_claims = getattr(
        artifact,
        "write_temporal_reference_claims",
    )
    load_claims = getattr(
        artifact,
        "load_temporal_reference_claims",
    )

    source_text = (
        "ARTICULO 1°: Aprobar la actualización de la Tabla "
        "“Honorarios de Referencia – Ciencias Informáticas” del ANEXO 1, "
        "para el cálculo de los honorarios y aportes profesionales "
        "con vigencia a partir del día 01 de septiembre de 2.026. "
        "ANEXO 1 – “Honorarios de Referencia – Ciencias Informáticas” "
        "Referencia: TÉCNICO HARDWARE/SOFTWARE ($/hora)$ 33.193"
    )

    raw_bytes = (
        bytes.fromhex("d0cf11e0a1b11ae1")
        + source_text.encode("utf-16le")
    )
    digest = hashlib.sha256(raw_bytes).hexdigest()

    claim = build_claim(
        raw_bytes,
        source_id="cpitlp_it_resolution_2026_09",
        source_url="https://example.test/resolution-11-26.doc",
        acquired_at="2026-09-04T19:16:53.530163+00:00",
        content_hash=digest,
        economic_object_raw="TÉCNICO HARDWARE/SOFTWARE ($/hora)",
        price_raw="$ 33.193",
    )

    assert claim is not None

    output = tmp_path / "temporal_reference_claims.jsonl"

    write_claims(
        output,
        (claim,),
    )

    rows = [
        json.loads(line)
        for line in output.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert len(rows) == 1
    assert rows[0]["schema_version"] == (
        "temporal-reference-claim-v1"
    )
    assert rows[0]["raw_document_id"] == (
        f"sha256:{digest}"
    )
    assert rows[0]["valid_from"] == "2026-09-01"
    assert rows[0]["valid_to"] is None

    # Evidence sidecar must not silently become a runtime freshness decision.
    assert "temporal_state" not in rows[0]
    assert "freshness_policy_known" not in rows[0]
    assert "freshness_policy_version" not in rows[0]

    loaded = load_claims(output)

    assert len(loaded) == 1
    restored = loaded[0]

    assert restored == claim
