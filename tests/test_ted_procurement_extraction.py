import json
from datetime import datetime, timezone

from src.aplicacion.extractor_contrataciones_ted import ExtractorContratacionesTed
from src.dominio.evidencia import DocumentoRaw
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


def _documento_raw(raw, storage_id=1):
    return DocumentoRaw(
        source="ted",
        source_record_id=raw.get("publication-number", "UNKNOWN"),
        source_url="https://ted.europa.eu/en/notice/123456-2026/xml",
        retrieved_at=datetime(2026, 8, 10, 15, 0, tzinfo=timezone.utc),
        content_type="application/json",
        raw_content=json.dumps(raw, ensure_ascii=False, sort_keys=True),
        content_hash="hash-1",
        metadata={},
        storage_id=storage_id,
    )


def _ted_raw(publication_number="123456-2026"):
    return {
        "publication-number": publication_number,
        "notice-title": {"eng": ["Cloud infrastructure services"]},
        "classification-cpv": ["72000000", "72250000"],
        "buyer-name": {"eng": ["Example buyer"]},
        "buyer-country": ["BEL"],
        "publication-date": "2026-08-10+02:00",
        "notice-type": ["cn-standard"],
        "procedure-type": ["open"],
        "links": {"xml": {"MUL": f"https://ted.europa.eu/en/notice/{publication_number}/xml"}},
    }


def test_extrae_identificador_titulo_y_cpv_desde_documento_ted():
    observacion = ExtractorContratacionesTed().extraer_uno(_documento_raw(_ted_raw()))

    assert observacion.extraction_status == "EXTRACTED"
    assert observacion.source_record_id == "123456-2026"
    assert observacion.title_raw == {"eng": ["Cloud infrastructure services"]}
    assert observacion.classification_raw == ["72000000", "72250000"]


def test_preserva_valor_moneda_y_semantica_si_el_raw_los_expone():
    raw = _ted_raw()
    raw["estimated-value-notice"] = "2500000"
    raw["estimated-value-notice-currency"] = "EUR"

    observacion = ExtractorContratacionesTed().extraer_uno(_documento_raw(raw))

    assert observacion.value_raw == "2500000"
    assert observacion.currency_raw == "EUR"
    assert observacion.value_semantics == "estimated_value"


def test_documento_sin_valor_sigue_siendo_observacion_valida_con_unknown():
    observacion = ExtractorContratacionesTed().extraer_uno(_documento_raw(_ted_raw()))

    assert observacion.extraction_status == "EXTRACTED"
    assert observacion.value_raw == "UNKNOWN"
    assert observacion.currency_raw == "UNKNOWN"
    assert observacion.value_semantics == "unknown_value_semantics"


def test_documento_malformed_se_rechaza_y_batch_continua(tmp_path):
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))
    malformed = _documento_raw({"notice-title": {"eng": ["no id"]}}, storage_id=1)
    valid = _documento_raw(_ted_raw("222222-2026"), storage_id=2)

    resultado = ExtractorContratacionesTed().extraer_lote([malformed, valid], repo)

    assert resultado.processed == 2
    assert resultado.extracted == 1
    assert resultado.rejected == 1
    assert repo.contar_observaciones_contratacion() == 1


def test_reextraer_mismo_raw_y_version_no_duplica(tmp_path):
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))
    documento = _documento_raw(_ted_raw(), storage_id=1)
    extractor = ExtractorContratacionesTed(extractor_version="ted-v1")

    extractor.extraer_lote([documento], repo)
    resultado = extractor.extraer_lote([documento], repo)

    assert resultado.extracted == 0
    assert resultado.duplicate == 1
    assert repo.contar_observaciones_contratacion() == 1
