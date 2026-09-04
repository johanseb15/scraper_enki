from datetime import datetime, timezone
import hashlib

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
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


def _observation(
    *,
    storage_id,
    raw_document_id,
    source,
    source_url,
    object_text,
    price_value,
):
    return RegistroPrecioComercialObservado(
        raw_document_id=raw_document_id,
        source=source,
        source_record_id=f"fixture-{storage_id}",
        source_url=source_url,
        extractor_version="fixture-extractor-v1",
        extraction_status="EXTRACTED",
        provider_raw="Fixture Provider",
        economic_object_raw=object_text,
        scope_raw="",
        price_raw=f"${price_value:,}".replace(",", "."),
        price_value=price_value,
        currency_raw="ARS",
        device_type_raw="",
        operating_system_raw="",
        backup_raw="",
        drivers_raw="",
        programs_raw="",
        license_raw="",
        modality_raw="",
        comparable_status="CANDIDATE",
        metadata={},
        storage_id=storage_id,
    )


def test_price_month_from_sibling_price_list_does_not_fan_out_to_other_offer():
    """
    A month/year may apply to one bounded price-list subsection but not to a
    separate sibling offer under the same broader section.

    Page/container scope must not be silently converted into offer applicability.
    """

    source = "fixture_temporal_sibling_scope"
    source_url = "https://example.test/services"

    raw_html = """
    <html>
      <body>
        <section id="services">
          <div class="dated-price-list">
            <h2>Precios orientativos — abril 2026</h2>
            <div class="offer">
              Soporte remoto por hora $30.000
            </div>
          </div>

          <div class="undated-price-list">
            <h2>Servicio presencial</h2>
            <div class="offer">
              Limpieza interna completa $65.000
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
            13,
            0,
            tzinfo=timezone.utc,
        ),
        content_type="text/html",
        raw_content=raw_html,
        content_hash=digest,
        metadata={},
        storage_id=9,
    )

    remote = _observation(
        storage_id=51,
        raw_document_id=9,
        source=source,
        source_url=source_url,
        object_text="Soporte remoto por hora",
        price_value=30000,
    )
    onsite = _observation(
        storage_id=52,
        raw_document_id=9,
        source=source,
        source_url=source_url,
        object_text="Limpieza interna completa",
        price_value=65000,
    )

    repository = FakeLiveTemporalRepository(
        documents=(raw_document,),
        observations=(remote, onsite),
    )

    evidence = build_live_temporal_evidence(
        repository=repository,
    )

    assert evidence["51"].price_validity_time_raw == "abril 2026"

    # Critical contract: the dated sibling list must not contaminate the
    # independent onsite offer merely because both share <section id=services>.
    assert evidence["52"].price_validity_time_raw is None
