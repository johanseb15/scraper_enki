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
):
    inserted = repo.guardar_observacion_precio_comercial(
        RegistroPrecioComercialObservado(
            raw_document_id=raw_document_id,
            source=source,
            source_record_id="masterfix-cleaning-28000",
            source_url=source_url,
            extractor_version="generic_price_extractor_v3",
            extraction_status="EXTRACTED",
            provider_raw="TecnoSoluciones",
            economic_object_raw=(
                "Limpieza + cambio de pasta térmica"
            ),
            scope_raw={
                "raw_context": (
                    "Limpieza + cambio de pasta térmica"
                ),
            },
            price_raw="$28000",
            price_value=28000,
            currency_raw="ARS",
            device_type_raw="PC",
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


def test_page_service_scope_is_preserved_without_becoming_offer_reach(
    tmp_path,
):
    """
    Regression based on the real MasterFix structure.

    An explicit provider/page service-scope statement lives in one
    section while several independently priced services live in a
    sibling section.

    The page-level claim is evidence worth preserving, but it must
    NOT become offer-applicable reach merely because both blocks are
    in the same document.
    """

    source = "fixture_masterfix_page_scope"
    source_url = "https://example.test/masterfix"

    html = """
    <html>
      <body>

        <section class="gradient-bg text-white">
          <div class="hero-copy">
            <h1>
              Servicio técnico de PC y notebooks
            </h1>

            <p>
              Servicio en toda CABA
            </p>
          </div>
        </section>

        <section class="pricing">
          <table>
            <tbody>

              <tr>
                <td>
                  Limpieza + cambio de pasta térmica
                </td>
                <td>
                  $28000
                </td>
              </tr>

              <tr>
                <td>
                  Formateo + Windows + programas básicos
                </td>
                <td>
                  $55000
                </td>
              </tr>

              <tr>
                <td>
                  Combo Limpieza + Formateo + Backup
                </td>
                <td>
                  $75000
                </td>
              </tr>

              <tr>
                <td>
                  Cambio de componente / Armado
                </td>
                <td>
                  $25000
                </td>
              </tr>

            </tbody>
          </table>
        </section>

      </body>
    </html>
    """

    digest = hashlib.sha256(
        html.encode("utf-8")
    ).hexdigest()

    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "enki_pricing.db")
    )

    inserted = repo.guardar_documento_raw(
        DocumentoRaw(
            source=source,
            source_record_id="masterfix-page",
            source_url=source_url,
            retrieved_at=datetime(
                2026,
                9,
                3,
                15,
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

    # Critical safety contract:
    # page-level CABA must NOT become offer-level reach.
    assert _values(
        evidence.claims,
        "geographic_reach",
    ) == set()

    # New evidence-retention contract:
    # preserve source truth without claiming applicability.
    assert _values(
        evidence.page_scope_claims,
        "geographic_reach",
    ) == {
        "NAMED_AREA:CABA",
    }

    page_claims = [
        claim
        for claim in evidence.page_scope_claims
        if claim.dimension == "geographic_reach"
    ]

    assert len(page_claims) == 1

    claim = page_claims[0]

    assert (
        "servicio en toda caba"
        in claim.raw_basis.casefold()
    )

    # The page-scope evidence must come from the scope block,
    # not from the pricing table or the whole document.
    assert (
        "limpieza + cambio"
        not in claim.raw_basis.casefold()
    )

    assert (
        "$28000"
        not in claim.raw_basis
    )

    assert claim.raw_document_id == (
        f"sha256:{digest}"
    )

    assert (
        "page-scope"
        in claim.provenance.casefold()
    )
