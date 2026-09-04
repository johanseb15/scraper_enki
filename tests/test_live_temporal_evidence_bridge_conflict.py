from datetime import datetime, timezone
import hashlib

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.dominio.temporal_evidence import TemporalEvidenceState
from src.infraestructura.live_temporal_evidence_bridge import (
    build_live_temporal_evidence,
)


class FakeLiveTemporalRepository:
    def __init__(self, *, documents, observations):
        self._documents = list(documents)
        self._observations = list(observations)

    def listar_documentos_raw(self, source=None, limit=None):
        documents = self._documents
        if source is not None:
            documents = [
                document
                for document in documents
                if document.source == source
            ]
        if limit is not None:
            documents = documents[:limit]
        return list(documents)

    def listar_observaciones_precios_comerciales(
        self,
        extractor_version=None,
        limit=None,
    ):
        observations = self._observations
        if extractor_version is not None:
            observations = [
                observation
                for observation in observations
                if observation.extractor_version
                == extractor_version
            ]
        if limit is not None:
            observations = observations[:limit]
        return list(observations)


def test_conflicting_nested_price_months_fail_closed_instead_of_picking_nearest():
    """
    Two different explicit month/year contexts on the exact offer ancestry are
    contradictory temporal claims. The bridge must preserve the conflict rather
    than silently choosing the nearest DOM ancestor.
    """

    source = "fixture_temporal_conflict"
    source_url = "https://example.test/pricing"

    raw_html = """
    <html>
      <body>
        <section class="annual-price-list">
          <h1>Lista de precios — mayo 2026</h1>

          <div class="service-price-list">
            <h2>Precios orientativos — abril 2026</h2>

            <div class="offer">
              Soporte remoto por hora $30.000
            </div>
          </div>
        </section>
      </body>
    </html>
    """.strip()

    digest = hashlib.sha256(
        raw_html.encode("utf-8")
    ).hexdigest()

    raw_document = DocumentoRaw(
        source=source,
        source_record_id=source_url,
        source_url=source_url,
        retrieved_at=datetime(
            2026,
            9,
            4,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        content_type="text/html",
        raw_content=raw_html,
        content_hash=digest,
        metadata={},
        storage_id=12,
    )

    observation = RegistroPrecioComercialObservado(
        raw_document_id=12,
        source=source,
        source_record_id="fixture-61",
        source_url=source_url,
        extractor_version="fixture-extractor-v1",
        extraction_status="EXTRACTED",
        provider_raw="Fixture Provider",
        economic_object_raw="Soporte remoto por hora",
        scope_raw="",
        price_raw="$30.000",
        price_value=30000,
        currency_raw="ARS",
        device_type_raw="",
        operating_system_raw="",
        backup_raw="",
        drivers_raw="",
        programs_raw="",
        license_raw="",
        modality_raw="REMOTO",
        comparable_status="CANDIDATE",
        metadata={},
        storage_id=61,
    )

    repository = FakeLiveTemporalRepository(
        documents=(raw_document,),
        observations=(observation,),
    )

    evidence = build_live_temporal_evidence(
        repository=repository,
    )["61"]

    assert evidence.price_validity_time_raw is None
    assert (
        evidence.temporal_state
        is TemporalEvidenceState.TEMPORAL_CONFLICT
    )
    assert evidence.temporal_identity_known is True
    assert evidence.freshness_policy_known is False
    assert evidence.conflicts == (
        "MULTIPLE_APPLICABLE_PRICE_TIME_CONTEXTS",
    )
