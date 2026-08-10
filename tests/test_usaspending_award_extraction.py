import json
from datetime import datetime, timezone

from src.aplicacion.extractor_usaspending_awards import ExtractorUSASpendingAwards
from src.dominio.evidencia import DocumentoRaw
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


def _raw_doc(raw, storage_id=1):
    return DocumentoRaw(
        source="usaspending",
        source_record_id=raw.get("generated_internal_id", "UNKNOWN"),
        source_url="https://www.usaspending.gov/award/CONT_AWD_1",
        retrieved_at=datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc),
        content_type="application/json",
        raw_content=json.dumps(raw, ensure_ascii=False, sort_keys=True),
        content_hash="hash-1",
        metadata={},
        storage_id=storage_id,
    )


def _award(record_id="CONT_AWD_1"):
    return {
        "generated_internal_id": record_id,
        "Award ID": "N001",
        "Recipient Name": "ACME TECH LLC",
        "Recipient UEI": "ABC123",
        "Award Amount": 125000.75,
        "Potential Award Amount": None,
        "Description": "SOFTWARE SUPPORT SERVICES",
        "Awarding Agency": "Department of Example",
        "Awarding Sub Agency": "Example Sub Agency",
        "Funding Agency": "Funding Department",
        "Funding Sub Agency": "Funding Sub Agency",
        "Contract Award Type": "DEFINITIVE CONTRACT",
        "Start Date": "2025-01-01",
        "End Date": "2025-12-31",
        "NAICS": {"code": "541512", "description": "COMPUTER SYSTEMS DESIGN SERVICES"},
        "PSC": {"code": "D302", "description": "IT AND TELECOM- SYSTEMS DEVELOPMENT"},
        "Place of Performance State Code": "VA",
        "Place of Performance Country Code": "USA",
    }


def test_extrae_award_observado_preservando_campos_clave():
    obs = ExtractorUSASpendingAwards().extraer_uno(_raw_doc(_award()))

    assert obs.extraction_status == "EXTRACTED"
    assert obs.source_record_id == "CONT_AWD_1"
    assert obs.recipient_raw == "ACME TECH LLC"
    assert obs.recipient_uei_raw == "ABC123"
    assert obs.award_amount_raw == 125000.75
    assert obs.naics_raw == {"code": "541512", "description": "COMPUTER SYSTEMS DESIGN SERVICES"}
    assert obs.psc_raw == {"code": "D302", "description": "IT AND TELECOM- SYSTEMS DEVELOPMENT"}
    assert obs.awarding_agency_raw == "Department of Example"


def test_raw_sin_descripcion_es_valido_con_unknown():
    raw = _award()
    raw["Description"] = None
    raw["Contract Description"] = None

    obs = ExtractorUSASpendingAwards().extraer_uno(_raw_doc(raw))

    assert obs.extraction_status == "EXTRACTED"
    assert obs.description_raw == "UNKNOWN"


def test_potential_award_amount_ausente_es_unknown_no_cero():
    raw = _award()
    raw["Potential Award Amount"] = None

    obs = ExtractorUSASpendingAwards().extraer_uno(_raw_doc(raw))

    assert obs.potential_award_amount_raw == "UNKNOWN"


def test_malformed_sin_identidad_estable_rechaza_y_batch_continua(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    malformed = _award()
    malformed.pop("generated_internal_id")
    valid = _award("CONT_AWD_2")

    result = ExtractorUSASpendingAwards().extraer_lote(
        [_raw_doc(malformed, 1), _raw_doc(valid, 2)], repo
    )

    assert result.processed == 2
    assert result.extracted == 1
    assert result.rejected == 1
    assert repo.contar_observaciones_usaspending_awards() == 1


def test_reextraer_mismo_raw_y_version_no_duplica(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    extractor = ExtractorUSASpendingAwards(extractor_version="usaspending_award_v1")
    doc = _raw_doc(_award(), 1)

    extractor.extraer_lote([doc], repo)
    result = extractor.extraer_lote([doc], repo)

    assert result.extracted == 0
    assert result.duplicate == 1
    assert repo.contar_observaciones_usaspending_awards() == 1
