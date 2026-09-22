import csv
import hashlib
from datetime import datetime, timezone

from src.aplicacion.semantic_normalization_live import (
    OUTPUT_FIELDS,
    _frozen_conflicts_with_explicit_backup_exclusion,
    build_semantic_rows,
)
from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


def test_frozen_composite_conflict_yields_to_explicit_sin_backup_live_semantics(
    tmp_path,
):
    """
    Un baseline histórico no debe dominar evidencia raw explícita cuando su
    interpretación contradice la semántica live vigente.

    "sin BackUp" excluye BACKUP_DATOS del servicio cobrado. El baseline se
    conserva intacto; esta prueba sólo exige que el bridge live no reutilice
    ciegamente esa interpretación histórica contradictoria.
    """
    source = "jadetech_generic"
    source_url = "https://fixture.example/jadetech"
    expression = (
        "Formateo e instalación de Sistema Operativo sin BackUp "
        "Categorías: Servicio técnico"
    )
    price_value = 42120

    db_path = tmp_path / "enki_pricing.db"
    repo = RepositorioSQLiteEvidencia(str(db_path))

    raw_html = f"<html><body>{expression} $42.120</body></html>"
    digest = hashlib.sha256(raw_html.encode("utf-8")).hexdigest()

    inserted = repo.guardar_documento_raw(
        DocumentoRaw(
            source=source,
            source_record_id="jadetech-page",
            source_url=source_url,
            retrieved_at=datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc),
            content_type="text/html",
            raw_content=raw_html,
            content_hash=digest,
            metadata={
                "provider_name": "Jadetech",
                "province": "CABA",
                "city": "CABA",
                "extractor_version": "generic_price_extractor_v3",
            },
        )
    )
    assert inserted is True

    raw_documents = repo.listar_documentos_raw(source=source)
    assert len(raw_documents) == 1
    raw_document = raw_documents[0]
    assert raw_document.storage_id is not None

    inserted = repo.guardar_observacion_precio_comercial(
        RegistroPrecioComercialObservado(
            raw_document_id=raw_document.storage_id,
            source=source,
            source_record_id="jadetech-formateo-sin-backup",
            source_url=source_url,
            extractor_version="generic_price_extractor_v3",
            extraction_status="EXTRACTED",
            provider_raw="Jadetech",
            economic_object_raw=expression,
            scope_raw={"raw_context": expression},
            price_raw="$42.120",
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
        )
    )
    assert inserted is True

    baseline_path = tmp_path / "semantic_normalization_v4.csv"
    frozen = {field: "" for field in OUTPUT_FIELDS}
    frozen.update(
        {
            "observation_id": "1",
            "source": source,
            "province": "CABA",
            "city": "CABA",
            "economic_object_raw": expression,
            "price_value": str(price_value),
            "currency": "ARS",
            "semantic_role": "COMPOSITE_SERVICE",
            "market_scope": "MIXED_OR_UNKNOWN",
            "matched_services": (
                "FORMATEO_INSTALACION_SO|BACKUP_DATOS"
            ),
            "canonical_service": "",
            "comparability_key": "",
            "original_comparable_status": "INDETERMINATE",
            "extractor_version": "frozen-v4",
        }
    )

    with baseline_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerow(frozen)

    rows, reused, newly_classified = build_semantic_rows(
        db_path,
        baseline_path=baseline_path,
    )

    assert len(rows) == 1
    assert reused == 0
    assert newly_classified == 1

    row = rows[0]
    assert row["semantic_role"] == "SINGLE_SERVICE"
    assert row["market_scope"] == "LOCAL_SERVICE"
    assert row["matched_services"] == "FORMATEO_INSTALACION_SO"
    assert row["canonical_service"] == "FORMATEO_INSTALACION_SO"
    assert row["comparability_key"] == "CABA::FORMATEO_INSTALACION_SO"


def test_presentation_badge_does_not_hide_explicit_backup_exclusion():
    frozen = {
        "matched_services": "FORMATEO_INSTALACION_SO|BACKUP_DATOS",
    }

    assert _frozen_conflicts_with_explicit_backup_exclusion(
        frozen,
        "Formateo e instalación de Sistema Operativo sin Más popular BackUp",
    ) is True

