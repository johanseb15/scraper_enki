from datetime import datetime, timezone
import hashlib

from src.aplicacion.runtime_cohort_lineage_gate import (
    evaluate_runtime_lineage,
)
from src.dominio.evidencia import DocumentoRaw
from src.dominio.offer_evidence import (
    EvidenceLineage,
    OfferReachChargedScopeEvidence,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


def test_runtime_lineage_accepts_reproducible_raw_stored_in_sqlite_without_file_export(
    tmp_path,
):
    raw_text = "<html><body>Servicio técnico $30000</body></html>"
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    db_path = tmp_path / "enki_pricing.db"
    repo = RepositorioSQLiteEvidencia(str(db_path))

    inserted = repo.guardar_documento_raw(
        DocumentoRaw(
            source="fixture_live",
            source_record_id="https://example.test/precios",
            source_url="https://example.test/precios",
            retrieved_at=datetime(
                2026,
                9,
                2,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            content_type="text/html",
            raw_content=raw_text,
            content_hash=digest,
            metadata={
                "provider_name": "Fixture Live",
                "extractor_version": "fixture-extractor-v1",
            },
        )
    )

    assert inserted is True

    stored = repo.listar_documentos_raw(
        source="fixture_live"
    )

    assert len(stored) == 1
    assert stored[0].raw_content == raw_text
    assert stored[0].content_hash == digest
    assert stored[0].storage_id is not None

    row = {
        "observation_id": "live-obs-1",
        "source": "fixture_live",
        "extractor_version": "fixture-extractor-v1",
    }

    evidence = OfferReachChargedScopeEvidence(
        observation_id="live-obs-1",
        lineage=EvidenceLineage(
            observation_id="live-obs-1",
            source_id="fixture_live",
            raw_document_id=f"sha256:{digest}",
            source_url="https://example.test/precios",
            acquired_at="2026-09-02T12:00:00+00:00",
            extractor_version="fixture-extractor-v1",
            provenance=f"sqlite:{db_path}#raw_documents/{stored[0].storage_id}",
            raw_document_path=None,
            raw_document_hash=digest,
            linkage_status="TRACEABLE_RAW",
        ),
        claims=(),
    )

    decision = evaluate_runtime_lineage(
        row,
        evidence,
        tmp_path,
        raw_repository=repo,
    )

    assert decision.admitted is True
    assert decision.lineage_status == "REPRODUCIBLE"
    assert decision.raw_document_id == f"sha256:{digest}"
    assert decision.raw_document_hash == digest

    # El RAW authoritative permanece en SQLite.
    assert not list(tmp_path.glob("*.html"))
