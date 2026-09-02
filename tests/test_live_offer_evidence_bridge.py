from datetime import datetime, timezone
import hashlib
import importlib

from src.aplicacion.runtime_cohort_lineage_gate import (
    build_runtime_cohort_rows,
)
from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


def _store_raw(
    repo,
    *,
    source,
    source_url,
    raw_text,
    retrieved_at,
):
    digest = hashlib.sha256(
        raw_text.encode("utf-8")
    ).hexdigest()

    inserted = repo.guardar_documento_raw(
        DocumentoRaw(
            source=source,
            source_record_id=source_url,
            source_url=source_url,
            retrieved_at=retrieved_at,
            content_type="text/html",
            raw_content=raw_text,
            content_hash=digest,
            metadata={
                "provider_name": "Fixture Live",
                "province": "Córdoba",
                "city": "Córdoba",
                "extractor_version": "fixture-extractor-v1",
            },
        )
    )

    assert inserted is True

    return digest


def test_live_offer_evidence_projection_follows_exact_sqlite_raw_document_fk(
    tmp_path,
):
    source = "fixture_live"
    source_url = "https://example.test/precios"

    db_path = tmp_path / "enki_pricing.db"
    repo = RepositorioSQLiteEvidencia(
        str(db_path)
    )

    old_digest = _store_raw(
        repo,
        source=source,
        source_url=source_url,
        raw_text=(
            "<html><body>"
            "Soporte remoto por hora $20000"
            "</body></html>"
        ),
        retrieved_at=datetime(
            2026,
            9,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    current_digest = _store_raw(
        repo,
        source=source,
        source_url=source_url,
        raw_text=(
            "<html><body>"
            "Soporte remoto por hora $30000"
            "</body></html>"
        ),
        retrieved_at=datetime(
            2026,
            9,
            2,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    documents = {
        document.content_hash: document
        for document in repo.listar_documentos_raw(
            source=source
        )
    }

    assert len(documents) == 2

    old_raw = documents[old_digest]
    current_raw = documents[current_digest]

    assert old_raw.storage_id is not None
    assert current_raw.storage_id is not None
    assert old_raw.storage_id != current_raw.storage_id

    inserted = repo.guardar_observacion_precio_comercial(
        RegistroPrecioComercialObservado(
            raw_document_id=current_raw.storage_id,
            source=source,
            source_record_id="service-1",
            source_url=source_url,
            extractor_version="fixture-extractor-v1",
            extraction_status="EXTRACTED",
            provider_raw="Fixture Live",
            economic_object_raw="Soporte remoto por hora",
            scope_raw="por hora",
            price_raw="$30000",
            price_value=30000,
            currency_raw="ARS",
            device_type_raw=None,
            operating_system_raw=None,
            backup_raw=None,
            drivers_raw=None,
            programs_raw=None,
            license_raw=None,
            modality_raw="remoto",
            comparable_status="CANDIDATE",
            metadata={},
        )
    )

    assert inserted is True

    observations = (
        repo.listar_observaciones_precios_comerciales()
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.storage_id is not None
    assert observation.raw_document_id == current_raw.storage_id

    # Import dentro del test para obtener un RED de ejecución,
    # no un error de collection.
    bridge = importlib.import_module(
        "src.infraestructura.live_offer_evidence_bridge"
    )

    evidence_by_observation = (
        bridge.build_live_offer_evidence(
            repository=repo,
        )
    )

    observation_id = str(
        observation.storage_id
    )

    assert observation_id in evidence_by_observation

    evidence = evidence_by_observation[
        observation_id
    ]

    lineage = evidence.lineage

    # La identidad semántica live debe ser el ID real de
    # commercial_price_observations.
    assert evidence.observation_id == observation_id
    assert lineage.observation_id == observation_id

    # Debe seguir el FK exacto hacia current_raw, no elegir
    # simplemente otro documento del mismo source.
    assert lineage.raw_document_hash == current_digest
    assert lineage.raw_document_hash != old_digest

    assert (
        lineage.raw_document_id
        == f"sha256:{current_digest}"
    )

    assert (
        lineage.raw_document_id
        != f"sha256:{old_digest}"
    )

    assert lineage.source_id == source
    assert lineage.source_url == source_url

    assert (
        lineage.acquired_at
        == current_raw.retrieved_at.isoformat()
    )

    assert (
        lineage.extractor_version
        == "fixture-extractor-v1"
    )

    assert lineage.raw_document_path is None
    assert lineage.linkage_status == "TRACEABLE_RAW"

    assert (
        f"raw_documents/{current_raw.storage_id}"
        in lineage.provenance
    )

    # La evidencia producida debe ser directamente consumible
    # por el runtime storage-neutral ya publicado.
    semantic_row = {
        "observation_id": observation_id,
        "source": source,
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "currency": "ARS",
        "canonical_service": "SOPORTE_REMOTO",
        "province": "",
        "price_value": "30000",
        "economic_object_raw": "Soporte remoto por hora",
        "extractor_version": "fixture-extractor-v1",
    }

    build = build_runtime_cohort_rows(
        (semantic_row,),
        evidence_by_observation,
        tmp_path,
        market_scope="REMOTE_NATIONAL_SERVICE",
        raw_repository=repo,
    )

    assert build.eligible_before == 1
    assert build.lineage_admitted == 1
    assert build.admitted == 1
    assert build.excluded == 0

    assert (
        build.decisions[0].raw_document_hash
        == current_digest
    )

    # El bridge no debe crear snapshots artificiales.
    assert not list(tmp_path.glob("*.html"))
