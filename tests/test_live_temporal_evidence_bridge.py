from datetime import datetime, timezone
import hashlib
import importlib

from src.aplicacion.temporal_evidence_admission_gate import (
    EXCLUSION_REASON_TEMPORAL_MISMATCH,
    evaluate_temporal_admission,
)
from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.dominio.temporal_evidence import TemporalEvidenceState


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


def test_live_temporal_bridge_preserves_explicit_price_month_without_promoting_current():
    """
    A live RAW document may explicitly anchor a price list to a month/year.

    That fact is economically temporal and should be preserved per observation,
    but it is NOT enough to claim that the price is CURRENT under the runtime
    pricing contract.
    """

    bridge = importlib.import_module(
        "src.infraestructura.live_temporal_evidence_bridge"
    )
    builder = getattr(
        bridge,
        "build_live_temporal_evidence",
    )

    source = "fixture_live_temporal"
    source_url = "https://example.test/precios"
    raw_html = """
    <html>
      <body>
        <section id="pricing">
          <h2>Lista de precios</h2>
          <p>Precios orientativos — abril 2026.</p>
          <div class="offer">
            Soporte remoto por hora $30.000
          </div>
        </section>
      </body>
    </html>
    """.strip()

    digest = hashlib.sha256(
        raw_html.encode("utf-8")
    ).hexdigest()
    acquired_at = datetime(
        2026,
        9,
        4,
        12,
        30,
        tzinfo=timezone.utc,
    )

    raw_document = DocumentoRaw(
        source=source,
        source_record_id=source_url,
        source_url=source_url,
        retrieved_at=acquired_at,
        content_type="text/html",
        raw_content=raw_html,
        content_hash=digest,
        metadata={
            "provider_name": "Fixture Provider",
            "extractor_version": "fixture-extractor-v1",
        },
        storage_id=7,
    )

    observation = RegistroPrecioComercialObservado(
        raw_document_id=7,
        source=source,
        source_record_id="fixture-offer-1",
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
        storage_id=41,
    )

    repository = FakeLiveTemporalRepository(
        documents=(raw_document,),
        observations=(observation,),
    )

    evidence_by_observation = builder(
        repository=repository,
    )

    assert set(evidence_by_observation) == {"41"}

    evidence = evidence_by_observation["41"]

    assert evidence.observation_id == "41"
    assert evidence.source_id == source
    assert evidence.extractor_version == "fixture-extractor-v1"
    assert evidence.raw_document_id == f"sha256:{digest}"
    assert evidence.acquired_at == acquired_at.isoformat()

    # This is the economically relevant temporal fact found in the price list.
    assert evidence.price_validity_time_raw == "abril 2026"

    # Exact RAW identity + acquired_at makes the observation reproducible
    # historically, but the bridge must never manufacture CURRENT freshness.
    assert (
        evidence.temporal_state
        is TemporalEvidenceState.HISTORICAL_REPRODUCIBLE
    )
    assert evidence.temporal_identity_known is True
    assert evidence.freshness_policy_known is False
    assert evidence.freshness_policy_version is None
    assert evidence.filesystem_dates_used_as_evidence is False

    decision = evaluate_temporal_admission(
        observation_id="41",
        evidence=evidence,
    )

    assert decision.admitted is False
    assert (
        decision.exclusion_reason
        == EXCLUSION_REASON_TEMPORAL_MISMATCH
    )
    assert (
        decision.exclusion_detail
        == "FRESHNESS_POLICY_UNKNOWN"
    )
