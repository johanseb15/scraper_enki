import json
from datetime import datetime, timezone

from src.aplicacion.colector_documentos_raw import ColectorDocumentosRaw
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


class ClienteFake:
    def __init__(self, records):
        self.records = records

    def buscar(self, *, query: str, limit: int):
        return self.records[:limit]


def _ted_record(publication_number="123456-2026", title="IT services"):
    return {
        "publication-number": publication_number,
        "notice-title": {"eng": [title]},
        "publication-date": "2026-08-10+02:00",
        "buyer-name": {"eng": ["Example buyer"]},
        "buyer-country": ["BEL"],
        "classification-cpv": ["72000000"],
        "links": {
            "xml": {
                "MUL": f"https://ted.europa.eu/en/notice/{publication_number}/xml"
            },
            "html": {
                "ENG": f"https://ted.europa.eu/en/notice/-/detail/{publication_number}"
            },
        },
    }


def test_collector_crea_raw_document_y_preserva_raw(tmp_path):
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))
    record = _ted_record()

    resultado = ColectorDocumentosRaw(
        cliente=ClienteFake([record]),
        repositorio=repo,
        fuente="ted",
        reloj=lambda: datetime(2026, 8, 10, 15, 0, tzinfo=timezone.utc),
    ).colectar(query="classification-cpv = 72000000", limit=1)

    assert resultado.accepted == 1
    documentos = repo.listar_documentos_raw(source="ted")
    assert len(documentos) == 1
    assert documentos[0].source_record_id == "123456-2026"
    assert documentos[0].source_url == "https://ted.europa.eu/en/notice/123456-2026/xml"
    assert json.loads(documentos[0].raw_content) == record


def test_collector_repetido_no_duplica_documento(tmp_path):
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))
    collector = ColectorDocumentosRaw(
        cliente=ClienteFake([_ted_record()]),
        repositorio=repo,
        fuente="ted",
    )

    collector.colectar(query="classification-cpv = 72000000", limit=1)
    resultado = collector.colectar(query="classification-cpv = 72000000", limit=1)

    assert resultado.accepted == 0
    assert resultado.duplicate == 1
    assert repo.contar_documentos_raw(source="ted") == 1


def test_registro_remoto_malformado_se_rechaza_y_el_batch_continua(tmp_path):
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))
    malformed = {"notice-title": {"eng": ["missing publication number"]}}

    resultado = ColectorDocumentosRaw(
        cliente=ClienteFake([malformed, _ted_record("222222-2026")]),
        repositorio=repo,
        fuente="ted",
    ).colectar(query="classification-cpv = 72000000", limit=2)

    assert resultado.accepted == 1
    assert resultado.rejected == 1
    assert resultado.failed == 0
    assert repo.contar_documentos_raw(source="ted") == 1


def test_registros_distintos_se_guardan_por_source_record_id(tmp_path):
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))

    resultado = ColectorDocumentosRaw(
        cliente=ClienteFake([_ted_record("111111-2026"), _ted_record("222222-2026")]),
        repositorio=repo,
        fuente="ted",
    ).colectar(query="classification-cpv = 72000000", limit=2)

    assert resultado.accepted == 2
    assert repo.contar_documentos_raw(source="ted") == 2
