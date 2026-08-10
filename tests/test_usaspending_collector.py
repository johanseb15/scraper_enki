from datetime import datetime, timezone

from src.aplicacion.colector_usaspending import ColectorUSASpending
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


class ClienteUSAFake:
    def __init__(self, awards):
        self.awards = awards

    def buscar_awards(self, *, limit: int):
        return self.awards[:limit]


def _award(record_id="CONT_AWD_1"):
    return {
        "generated_internal_id": record_id,
        "Award ID": "N001",
        "Recipient Name": "ACME TECH LLC",
        "Recipient UEI": "ABC123",
        "Award Amount": 125000.75,
        "Potential Award Amount": 250000.00,
        "Description": "SOFTWARE SUPPORT SERVICES",
        "Awarding Agency": "Department of Example",
        "Awarding Sub Agency": "Example Office",
        "Start Date": "2025-01-01",
        "End Date": "2025-12-31",
        "NAICS": {"code": "541512", "description": "COMPUTER SYSTEMS DESIGN SERVICES"},
        "PSC": {"code": "D302", "description": "IT AND TELECOM- SYSTEMS DEVELOPMENT"},
        "Place of Performance State Code": "VA",
        "Place of Performance Country Code": "USA",
    }


def test_usaspending_real_shaped_award_crea_raw_document(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))

    resultado = ColectorUSASpending(
        cliente=ClienteUSAFake([_award()]),
        repositorio=repo,
        reloj=lambda: datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc),
    ).colectar(limit=1)

    assert resultado.accepted == 1
    docs = repo.listar_documentos_raw(source="usaspending")
    assert len(docs) == 1
    assert docs[0].source_record_id == "CONT_AWD_1"
    assert docs[0].metadata["value_semantics"] == "award_total"
    assert docs[0].metadata["classification_raw"] == {
        "NAICS": {"code": "541512", "description": "COMPUTER SYSTEMS DESIGN SERVICES"},
        "PSC": {"code": "D302", "description": "IT AND TELECOM- SYSTEMS DEVELOPMENT"},
    }


def test_usaspending_rerun_no_duplica(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    collector = ColectorUSASpending(ClienteUSAFake([_award()]), repo)

    collector.colectar(limit=1)
    resultado = collector.colectar(limit=1)

    assert resultado.accepted == 0
    assert resultado.duplicate == 1
    assert repo.contar_documentos_raw(source="usaspending") == 1


def test_usaspending_malformed_rejected_batch_continues(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    malformed = {"Recipient Name": "NO ID"}

    resultado = ColectorUSASpending(
        ClienteUSAFake([malformed, _award("CONT_AWD_2")]), repo
    ).colectar(limit=2)

    assert resultado.requested == 2
    assert resultado.downloaded == 2
    assert resultado.accepted == 1
    assert resultado.rejected == 1
    assert resultado.failed == 0
    assert repo.contar_documentos_raw(source="usaspending") == 1
