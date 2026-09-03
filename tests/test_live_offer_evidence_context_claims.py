from datetime import datetime, timezone
import hashlib

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.infraestructura.live_offer_evidence_bridge import (
    build_live_offer_evidence,
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
            scope_raw={
                "raw_context": economic_object_raw,
            },
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


def _claim_values(evidence, dimension):
    return {
        claim.value
        for claim in evidence.claims
        if claim.dimension == dimension
    }


def test_live_offer_evidence_projects_only_offer_applicable_raw_context(
    tmp_path,
):
    source = "fixture_contextual_reach"
    source_url = "https://example.test/servicios"

    html = """
    <html>
      <body>

        <section id="remote-support">
          <h2>Soporte remoto para empresas</h2>

          <p>
            Servicio de soporte con cobertura nacional.
          </p>

          <div class="offer">
            <span>
              Conexión Remota x 1 HS PC-Notebook-AIO
            </span>
            <strong>$30000</strong>
          </div>
        </section>

        <section id="local-maintenance">
          <h2>Mantenimiento presencial en taller</h2>

          <div class="offer">
            <span>
              Limpieza física y cambio de pasta térmica
            </span>
            <strong>$28000</strong>
          </div>
        </section>

        <footer>
          Envíos de productos a todo el país por correo.
        </footer>

      </body>
    </html>
    """

    digest = hashlib.sha256(
        html.encode("utf-8")
    ).hexdigest()

    db_path = tmp_path / "enki_pricing.db"

    repo = RepositorioSQLiteEvidencia(
        str(db_path)
    )

    inserted = repo.guardar_documento_raw(
        DocumentoRaw(
            source=source,
            source_record_id="fixture-page",
            source_url=source_url,
            retrieved_at=datetime(
                2026,
                9,
                3,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            content_type="text/html",
            raw_content=html,
            content_hash=digest,
            metadata={},
        )
    )

    assert inserted is True

    raw_documents = repo.listar_documentos_raw(
        source=source
    )

    assert len(raw_documents) == 1

    raw_document = raw_documents[0]

    assert raw_document.storage_id is not None

    _save_observation(
        repo,
        raw_document_id=raw_document.storage_id,
        source=source,
        source_url=source_url,
        source_record_id="remote-support-30000",
        economic_object_raw=(
            "Conexión Remota x 1 HS PC-Notebook-AIO"
        ),
        price_value=30000,
    )

    _save_observation(
        repo,
        raw_document_id=raw_document.storage_id,
        source=source,
        source_url=source_url,
        source_record_id="local-maintenance-28000",
        economic_object_raw=(
            "Limpieza física y cambio de pasta térmica"
        ),
        price_value=28000,
    )

    observations = (
        repo.listar_observaciones_precios_comerciales()
    )

    assert len(observations) == 2

    by_object = {
        str(observation.economic_object_raw):
        observation
        for observation in observations
    }

    remote_observation = by_object[
        "Conexión Remota x 1 HS PC-Notebook-AIO"
    ]

    local_observation = by_object[
        "Limpieza física y cambio de pasta térmica"
    ]

    assert remote_observation.storage_id is not None
    assert local_observation.storage_id is not None

    evidence = build_live_offer_evidence(
        repository=repo,
    )

    remote_evidence = evidence[
        str(remote_observation.storage_id)
    ]

    local_evidence = evidence[
        str(local_observation.storage_id)
    ]

    remote_reach_claims = [
        claim
        for claim in remote_evidence.claims
        if claim.dimension == "geographic_reach"
    ]

    # The offer-local section explicitly states service
    # coverage. This must become attributable source evidence.
    assert {
        claim.value
        for claim in remote_reach_claims
    } == {"NATIONAL"}

    assert len(remote_reach_claims) == 1

    reach_claim = remote_reach_claims[0]

    assert (
        "cobertura nacional"
        in reach_claim.raw_basis.casefold()
    )

    assert (
        reach_claim.raw_document_id
        == f"sha256:{digest}"
    )

    # The other offer shares the exact same RAW document,
    # but NATIONAL applies to the remote-support section,
    # not to the maintenance offer.
    assert (
        "NATIONAL"
        not in _claim_values(
            local_evidence,
            "geographic_reach",
        )
    )

    # Product shipping language must never establish
    # service reach for the local maintenance offer.
    assert all(
        "envíos de productos"
        not in claim.raw_basis.casefold()
        for claim in local_evidence.claims
        if claim.dimension == "geographic_reach"
    )


def test_live_offer_evidence_uses_bounded_context_when_raw_contains_one_exact_offer(
    tmp_path,
):
    """
    Real-structure regression based on Taja Service.

    The navigation contains an exact text duplicate of the economic object,
    but it is not the priced offer.

    The real offer is represented by a larger heading containing both the
    economic object and the price. A page-local service-reach statement is
    outside that immediate section but inside the same bounded main content.

    Since this RAW contains exactly one reproducible price observation,
    that bounded context can safely be attributed to the offer.
    """

    source = "fixture_taja_real_dom"
    source_url = "https://example.test/servicio-a-domicilio"

    html = """
    <html>
      <body>

        <nav>
          <ul>
            <li>
              <a href="/servicio-a-domicilio">
                <span>
                  Servicio Técnico a Domicilio
                </span>
              </a>
            </li>
          </ul>
        </nav>

        <main class="page-content">

          <div class="service-page">

            <div class="page-heading">
              <p>
                Soporte Técnico de PC y Notebook en CABA
              </p>
            </div>

            <section class="priced-service">

              <div>
                <h1>
                  <strong>Servicio Técnico</strong>
                  <strong>a Domicilio</strong>
                  <strong>Desde $9000</strong>
                </h1>
              </div>

              <p>
                Arreglos de computadoras y notebooks
                a domicilio por técnico profesional.
              </p>

            </section>

          </div>

        </main>

        <footer>
          Envíos de productos a todo el país por correo.
        </footer>

      </body>
    </html>
    """

    digest = hashlib.sha256(
        html.encode("utf-8")
    ).hexdigest()

    db_path = tmp_path / "enki_pricing.db"

    repo = RepositorioSQLiteEvidencia(
        str(db_path)
    )

    inserted = repo.guardar_documento_raw(
        DocumentoRaw(
            source=source,
            source_record_id="fixture-taja-page",
            source_url=source_url,
            retrieved_at=datetime(
                2026,
                9,
                3,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            content_type="text/html",
            raw_content=html,
            content_hash=digest,
            metadata={},
        )
    )

    assert inserted is True

    raw_documents = repo.listar_documentos_raw(
        source=source
    )

    assert len(raw_documents) == 1

    raw_document = raw_documents[0]

    assert raw_document.storage_id is not None

    _save_observation(
        repo,
        raw_document_id=raw_document.storage_id,
        source=source,
        source_url=source_url,
        source_record_id="taja-domicilio-9000",
        economic_object_raw=(
            "Servicio Técnico a Domicilio"
        ),
        price_value=9000,
    )

    observations = (
        repo.listar_observaciones_precios_comerciales()
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.storage_id is not None

    evidence = build_live_offer_evidence(
        repository=repo,
    )[
        str(observation.storage_id)
    ]

    reach_claims = [
        claim
        for claim in evidence.claims
        if claim.dimension
        == "geographic_reach"
    ]

    assert {
        claim.value
        for claim in reach_claims
    } == {
        "NAMED_AREA:CABA",
    }

    assert len(reach_claims) == 1

    reach = reach_claims[0]

    assert (
        "soporte técnico de pc y notebook en caba"
        in reach.raw_basis.casefold()
    )

    assert (
        "servicio técnico"
        in reach.raw_basis.casefold()
    )

    assert reach.raw_document_id == (
        f"sha256:{digest}"
    )

    # The exact-text navigation item cannot establish offer identity.
    assert "menu" not in reach.provenance.casefold()

    # Product shipping remains outside the bounded service context.
    assert (
        "envíos de productos"
        not in reach.raw_basis.casefold()
    )
