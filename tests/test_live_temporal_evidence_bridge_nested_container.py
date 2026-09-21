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


def test_nested_price_container_keeps_its_shared_price_month():
    """
    Real live pages commonly wrap a whole price list in a broad section and put
    the actual list header + offers inside a nested container.

    The temporal bridge must not anchor at the broad section merely because
    re-running the generic extractor there can reproduce the persisted offer.
    It must preserve the nearest bounded list context that still reproduces the
    offer, so an explicit shared month/year is not pruned as a price-bearing
    sibling branch.
    """

    source = "fixture_temporal_nested_container"
    source_url = "https://example.test/mantenimiento"

    raw_html = """
    <html>
      <body>
        <section id="precios">
          <div class="container">
            <div class="label">Lista de precios</div>
            <h2>Precios orientativos — abril 2026.</h2>

            <div class="offers">
              <div class="offer">
                Formateo e instalación de SO sin backup PC Notebook $49.700
              </div>
              <div class="offer">
                Limpieza + Formateo + Programas básicos $77.300
              </div>
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
            15,
            0,
            tzinfo=timezone.utc,
        ),
        content_type="text/html",
        raw_content=raw_html,
        content_hash=digest,
        metadata={},
        storage_id=20,
    )

    observation = RegistroPrecioComercialObservado(
        raw_document_id=20,
        source=source,
        source_record_id="fixture-71",
        source_url=source_url,
        extractor_version="fixture-extractor-v1",
        extraction_status="EXTRACTED",
        provider_raw="Fixture Provider",
        economic_object_raw=(
            "Formateo e instalación de SO sin backup PC Notebook"
        ),
        scope_raw="",
        price_raw="$49.700",
        price_value=49700,
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
        storage_id=71,
    )

    repository = FakeLiveTemporalRepository(
        documents=(raw_document,),
        observations=(observation,),
    )

    evidence = build_live_temporal_evidence(
        repository=repository,
    )["71"]

    assert evidence.price_validity_time_raw == "abril 2026"
