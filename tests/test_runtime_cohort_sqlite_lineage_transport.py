from datetime import datetime, timezone
import hashlib

from src.aplicacion.runtime_cohort_lineage_gate import (
    build_runtime_cohort_rows,
)
from src.dominio.evidencia import DocumentoRaw
from src.dominio.offer_evidence import (
    EvidenceLineage,
    OfferReachChargedScopeEvidence,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


def test_runtime_cohort_builder_transports_sqlite_raw_repository_to_lineage_gate(
    tmp_path,
):
    raw_text = "<html><body>Soporte remoto por hora $30000</body></html>"
    digest = hashlib.sha256(
        raw_text.encode("utf-8")
    ).hexdigest()

    db_path = tmp_path / "enki_pricing.db"
    repo = RepositorioSQLiteEvidencia(
        str(db_path)
    )

    inserted = repo.guardar_documento_raw(
        DocumentoRaw(
            source="fixture_live",
            source_record_id="https://example.test/soporte",
            source_url="https://example.test/soporte",
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
    assert stored[0].storage_id is not None

    row = {
        "observation_id": "live-obs-1",
        "source": "fixture_live",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "currency": "ARS",
        "canonical_service": "SOPORTE_REMOTO",
        "province": "",
        "price_value": "30000",
        "economic_object_raw": "Soporte remoto por hora",
        "extractor_version": "fixture-extractor-v1",
    }

    evidence = OfferReachChargedScopeEvidence(
        observation_id="live-obs-1",
        lineage=EvidenceLineage(
            observation_id="live-obs-1",
            source_id="fixture_live",
            raw_document_id=f"sha256:{digest}",
            source_url="https://example.test/soporte",
            acquired_at="2026-09-02T12:00:00+00:00",
            extractor_version="fixture-extractor-v1",
            provenance=(
                f"sqlite:{db_path}"
                f"#raw_documents/{stored[0].storage_id}"
            ),
            raw_document_path=None,
            raw_document_hash=digest,
            linkage_status="TRACEABLE_RAW",
        ),
        claims=(),
    )

    build = build_runtime_cohort_rows(
        (row,),
        {"live-obs-1": evidence},
        tmp_path,
        market_scope="REMOTE_NATIONAL_SERVICE",
        raw_repository=repo,
    )

    assert build.eligible_before == 1
    assert build.lineage_admitted == 1
    assert build.admitted == 1
    assert build.excluded == 0

    assert len(build.decisions) == 1
    assert build.decisions[0].admitted is True
    assert build.decisions[0].lineage_status == "REPRODUCIBLE"

    assert len(build.cohorts) == 1
    assert build.cohorts[0]["observation_ids"] == "live-obs-1"

    # El cohort builder tampoco debe materializar RAW a filesystem.
    assert not list(tmp_path.glob("*.html"))
