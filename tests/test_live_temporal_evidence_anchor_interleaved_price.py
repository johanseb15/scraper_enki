from datetime import datetime, timezone
import hashlib

from bs4 import BeautifulSoup

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
import src.infraestructura.live_temporal_evidence_bridge as bridge


def test_offer_anchor_survives_primary_price_interleaved_inside_row(monkeypatch):
    """
    A persisted economic_object_raw may omit the primary extracted price even
    when that price is physically interleaved inside the DOM row.

    Example live geometry:
        Servicio técnico a domicilio $44.000 Hora Inicial ... $28.000 adicional

    Persisted interpretation:
        object = "Servicio técnico a domicilio Hora Inicial ... $28.000 adicional"
        price  = $44.000

    The cheap DOM prefilter must not reject the correct <tr> before the generic
    extractor can reproduce the persisted observation exactly.
    """

    source = "fixture_interleaved_primary_price"
    source_url = "https://example.test/precios"

    raw_html = """
    <html>
      <body>
        <div id="listaPrecios">
          <a>TABLA DE HONORARIOS SERVICIO TECNICO MARZO 2025</a>

          <table>
            <tbody>
              <tr>
                <td>Servicio técnico a domicilio (sólo empresas)</td>
                <td>
                  $ 44.000 Hora Inicial ó fracción
                  $ 28.000 Hora adicional
                </td>
              </tr>
            </tbody>
          </table>
        </div>
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
            16,
            0,
            tzinfo=timezone.utc,
        ),
        content_type="text/html",
        raw_content=raw_html,
        content_hash=digest,
        metadata={},
        storage_id=40,
    )

    observation = RegistroPrecioComercialObservado(
        raw_document_id=40,
        source=source,
        source_record_id="fixture-91",
        source_url=source_url,
        extractor_version="fixture-extractor-v1",
        extraction_status="EXTRACTED",
        provider_raw="Fixture Provider",
        economic_object_raw=(
            "Servicio técnico a domicilio (sólo empresas) "
            "Hora Inicial ó fracción $ 28.000 Hora adicional"
        ),
        scope_raw="",
        price_raw="$ 44.000",
        price_value=44000,
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
        storage_id=91,
    )

    soup = BeautifulSoup(
        raw_html,
        "html.parser",
    )

    calls = []

    def fake_observations_in_container(
        container,
        *,
        observation,
        raw_document,
    ):
        calls.append(container.name)

        if container.name == "tr":
            return [observation]

        return []

    monkeypatch.setattr(
        bridge,
        "_observations_in_container",
        fake_observations_in_container,
    )

    anchor = bridge._find_offer_anchor(
        observation,
        raw_document=raw_document,
        soup=soup,
    )

    assert anchor is not None
    assert anchor.name == "tr"

    # The causal contract: the real row must reach exact re-extraction rather
    # than being discarded by the raw-text substring prefilter.
    assert "tr" in calls
