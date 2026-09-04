from datetime import datetime, timezone
import hashlib

from bs4 import BeautifulSoup

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
import src.infraestructura.live_temporal_evidence_bridge as bridge


def test_offer_anchor_prefers_deepest_reproducing_dom_node(monkeypatch):
    """
    When multiple nested DOM nodes can all reproduce the same persisted offer,
    the temporal bridge must choose the most specific (deepest) one.

    Returning the first broad ancestor causes legitimate temporal header branches
    to be treated as unrelated price-bearing siblings and pruned.
    """

    source = "fixture_anchor_specificity"
    source_url = "https://example.test/precios"

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
            30,
            tzinfo=timezone.utc,
        ),
        content_type="text/html",
        raw_content=raw_html,
        content_hash=digest,
        metadata={},
        storage_id=30,
    )

    observation = RegistroPrecioComercialObservado(
        raw_document_id=30,
        source=source,
        source_record_id="fixture-81",
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
        storage_id=81,
    )

    soup = BeautifulSoup(
        raw_html,
        "html.parser",
    )

    def fake_observations_in_container(
        container,
        *,
        observation,
        raw_document,
    ):
        # Reproduce the live failure condition deliberately: the generic
        # extractor can reconstruct the same persisted offer from several
        # nested scopes, including a broad section.
        if (
            "Formateo e instalación de SO sin backup PC Notebook"
            in container.get_text(" ", strip=True)
        ):
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
    assert anchor.name == "div"
    assert "offer" in (anchor.get("class") or [])
