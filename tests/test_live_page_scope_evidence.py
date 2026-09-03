from datetime import datetime, timezone
import hashlib
import importlib

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


def _save_observation(
    repo,
    *,
    raw_document_id,
    source,
    source_url,
    source_record_id,
    economic_object_raw,
    price_value,
):
    inserted = repo.guardar_observacion_precio_comercial(
        RegistroPrecioComercialObservado(
            raw_document_id=raw_document_id,
            source=source,
            source_record_id=source_record_id,
            source_url=source_url,
            extractor_version="generic_price_extractor_v3",
            extraction_status="EXTRACTED",
            provider_raw="Fixture Provider",
            economic_object_raw=economic_object_raw,
            scope_raw={"raw_context": economic_object_raw},
            price_raw=f"${price_value}",
            price_value=price_value,
            currency_raw="ARS",
            device_type_raw="UNKNOWN",
            operating_system_raw="UNKNOWN",
            backup_raw="UNKNOWN",
            drivers_raw="UNKNOWN",
            programs_raw="UNKNOWN",
            license_raw="UNKNOWN",
            modality_raw="UNKNOWN",
            comparable_status="INDETERMINATE",
            metadata={},
            rejection_reason="",
        )
    )
    assert inserted is True


def _values(claims, dimension):
    return {
        claim.value
        for claim in claims
        if claim.dimension == dimension
    }


def _save_raw(repo, *, source, source_url, html):
    digest = hashlib.sha256(html.encode("utf-8")).hexdigest()

    inserted = repo.guardar_documento_raw(
        DocumentoRaw(
            source=source,
            source_record_id=f"{source}-page",
            source_url=source_url,
            retrieved_at=datetime(
                2026, 9, 3, 12, 0, tzinfo=timezone.utc
            ),
            content_type="text/html",
            raw_content=html,
            content_hash=digest,
            metadata={},
        )
    )
    assert inserted is True

    raw_documents = repo.listar_documentos_raw(source=source)
    assert len(raw_documents) == 1
    raw_document = raw_documents[0]
    assert raw_document.storage_id is not None

    return raw_document, f"sha256:{digest}"


def test_page_service_scope_is_preserved_without_becoming_offer_reach(
    tmp_path,
):
    bridge = importlib.import_module(
        "src.infraestructura.live_offer_evidence_bridge"
    )

    source = "fixture_masterfix_page_scope"
    source_url = "https://example.test/masterfix"

    html = """
    <html>
      <body>
        <section id="hero">
          <h1>Servicio técnico de PC y notebooks</h1>
          <p>Servicio en toda CABA</p>
        </section>

        <section id="pricing">
          <div class="offer">
            <span>Limpieza y mantenimiento PC</span>
            <strong>$28000</strong>
          </div>
          <div class="offer">
            <span>Formateo e instalación Windows</span>
            <strong>$35000</strong>
          </div>
          <div class="offer">
            <span>Backup y recuperación</span>
            <strong>$42000</strong>
          </div>
          <div class="offer">
            <span>Diagnóstico técnico</span>
            <strong>$20000</strong>
          </div>
        </section>
      </body>
    </html>
    """

    db_path = tmp_path / "enki_pricing.db"
    repo = RepositorioSQLiteEvidencia(str(db_path))

    raw_document, raw_id = _save_raw(
        repo,
        source=source,
        source_url=source_url,
        html=html,
    )

    _save_observation(
        repo,
        raw_document_id=raw_document.storage_id,
        source=source,
        source_url=source_url,
        source_record_id="masterfix-limpieza-28000",
        economic_object_raw="Limpieza y mantenimiento PC",
        price_value=28000,
    )

    observations = repo.listar_observaciones_precios_comerciales()
    assert len(observations) == 1

    observation = observations[0]
    assert observation.storage_id is not None

    offer_evidence = bridge.build_live_offer_evidence(
        repository=repo,
    )[str(observation.storage_id)]

    assert _values(
        offer_evidence.claims,
        "geographic_reach",
    ) == set()

    page_scope_by_raw = bridge.build_live_page_scope_evidence(
        repository=repo,
    )

    page_scope = page_scope_by_raw[raw_id]

    assert page_scope.raw_document_id == raw_id
    assert _values(
        page_scope.claims,
        "geographic_reach",
    ) == {"NAMED_AREA:CABA"}

    assert all(
        not hasattr(claim, "observation_id")
        for claim in page_scope.claims
    )


def test_logistics_service_in_caba_is_not_page_service_scope(
    tmp_path,
):
    bridge = importlib.import_module(
        "src.infraestructura.live_offer_evidence_bridge"
    )

    source = "fixture_logistics_page_scope"
    source_url = "https://example.test/logistics"

    html = """
    <html>
      <body>
        <section id="pricing">
          <div class="offer">
            <span>Limpieza y mantenimiento PC</span>
            <strong>$28000</strong>
          </div>
        </section>

        <section id="entregas">
          <h2>Entregas de insumos y repuestos</h2>
          <p>
            Servicio de cadetería y distribución en toda CABA.
          </p>
        </section>
      </body>
    </html>
    """

    db_path = tmp_path / "enki_pricing.db"
    repo = RepositorioSQLiteEvidencia(str(db_path))

    _, raw_id = _save_raw(
        repo,
        source=source,
        source_url=source_url,
        html=html,
    )

    page_scope = bridge.build_live_page_scope_evidence(
        repository=repo,
    )[raw_id]

    assert _values(
        page_scope.claims,
        "geographic_reach",
    ) == set()


def test_provider_contact_location_is_not_page_service_scope(
    tmp_path,
):
    """
    A provider may state where its workshop/office is located using service
    language. That establishes provider location or walk-in context, not a
    service-coverage claim for the page's priced offers.
    """

    bridge = importlib.import_module(
        "src.infraestructura.live_offer_evidence_bridge"
    )

    source = "fixture_provider_location_page_scope"
    source_url = "https://example.test/provider-location"

    html = """
    <html>
      <body>
        <section id="pricing">
          <div class="offer">
            <span>Reparación de notebook</span>
            <strong>$50000</strong>
          </div>
        </section>

        <section id="contacto">
          <h2>Nuestro laboratorio</h2>
          <p>
            Servicio técnico en CABA.
          </p>
          <p>
            Atención exclusivamente en nuestro laboratorio.
            No realizamos visitas a domicilio.
          </p>
          <p>
            Av. Corrientes 1234, Ciudad de Buenos Aires.
          </p>
        </section>
      </body>
    </html>
    """

    db_path = tmp_path / "enki_pricing.db"
    repo = RepositorioSQLiteEvidencia(str(db_path))

    _, raw_id = _save_raw(
        repo,
        source=source,
        source_url=source_url,
        html=html,
    )

    page_scope = bridge.build_live_page_scope_evidence(
        repository=repo,
    )[raw_id]

    assert _values(
        page_scope.claims,
        "geographic_reach",
    ) == set()


def test_conflicting_page_service_scopes_fail_closed(
    tmp_path,
):
    """
    One RAW document may describe different service families with different
    reaches. Until page->offer applicability exists, document-level page scope
    must not expose both scopes as if they were one unambiguous service truth.
    """

    bridge = importlib.import_module(
        "src.infraestructura.live_offer_evidence_bridge"
    )

    source = "fixture_conflicting_page_scope"
    source_url = "https://example.test/mixed-services"

    html = """
    <html>
      <body>
        <section id="local-service">
          <h2>Servicio técnico presencial</h2>
          <p>Servicio en toda CABA.</p>
        </section>

        <section id="remote-service">
          <h2>Soporte remoto para empresas</h2>
          <p>Servicio de soporte con cobertura nacional.</p>
        </section>

        <section id="pricing">
          <div class="offer">
            <span>Limpieza y mantenimiento PC</span>
            <strong>$28000</strong>
          </div>
          <div class="offer">
            <span>Soporte remoto por hora</span>
            <strong>$30000</strong>
          </div>
        </section>
      </body>
    </html>
    """

    db_path = tmp_path / "enki_pricing.db"
    repo = RepositorioSQLiteEvidencia(str(db_path))

    _, raw_id = _save_raw(
        repo,
        source=source,
        source_url=source_url,
        html=html,
    )

    page_scope = bridge.build_live_page_scope_evidence(
        repository=repo,
    )[raw_id]

    # Without a proven page->offer relationship, conflicting geographic
    # scopes must fail closed at document level.
    assert _values(
        page_scope.claims,
        "geographic_reach",
    ) == set()
