from datetime import datetime, timezone

from src.aplicacion.colector_ted_full_notices import ColectorTedFullNotices
from src.dominio.evidencia import DocumentoRaw
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


class ClienteFullFake:
    def __init__(self, responses):
        self.responses = responses

    def obtener(self, documento):
        response = self.responses[documento.source_record_id]
        if isinstance(response, Exception):
            raise response
        return response


def _search_doc(record_id="123456-2026", storage_id=1):
    return DocumentoRaw(
        source="ted",
        source_record_id=record_id,
        source_url=f"https://ted.europa.eu/en/notice/{record_id}/xml",
        retrieved_at=datetime(2026, 8, 10, 15, 0, tzinfo=timezone.utc),
        content_type="application/json",
        raw_content='{"publication-number":"%s"}' % record_id,
        content_hash="search-hash",
        metadata={"document_kind": "TED_SEARCH_RESULT"},
        storage_id=storage_id,
    )


def test_full_notice_fetch_guarda_documento_raw_xml(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    cliente = ClienteFullFake({"123456-2026": (200, "application/xml", "<notice><id>123456-2026</id></notice>", {})})

    resultado = ColectorTedFullNotices(cliente=cliente, repositorio=repo).enriquecer([_search_doc()])

    assert resultado.accepted == 1
    docs = repo.listar_documentos_raw(source="ted_full_notice")
    assert len(docs) == 1
    assert docs[0].source_record_id == "123456-2026"
    assert docs[0].content_type == "application/xml"
    assert docs[0].raw_content == "<notice><id>123456-2026</id></notice>"
    assert docs[0].metadata["related_search_document_id"] == 1


def test_full_notice_fetch_repetido_no_duplica(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    cliente = ClienteFullFake({"123456-2026": (200, "application/xml", "<notice/>", {})})
    collector = ColectorTedFullNotices(cliente=cliente, repositorio=repo)

    collector.enriquecer([_search_doc()])
    resultado = collector.enriquecer([_search_doc()])

    assert resultado.accepted == 0
    assert resultado.duplicate == 1
    assert repo.contar_documentos_raw(source="ted_full_notice") == 1


def test_full_notice_not_available_por_202_continua_batch(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    cliente = ClienteFullFake({
        "blocked-2026": (202, "text/html; charset=UTF-8", "", {"x-amzn-waf-action": "challenge"}),
        "ok-2026": (200, "application/xml", "<notice/>", {}),
    })

    resultado = ColectorTedFullNotices(cliente=cliente, repositorio=repo).enriquecer([
        _search_doc("blocked-2026", 1),
        _search_doc("ok-2026", 2),
    ])

    assert resultado.requested == 2
    assert resultado.accepted == 1
    assert resultado.not_available == 1
    assert resultado.failed == 0
    assert repo.contar_documentos_raw(source="ted_full_notice") == 1


def test_full_notice_error_transitorio_no_detiene_batch(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    cliente = ClienteFullFake({
        "fail-2026": RuntimeError("timeout"),
        "ok-2026": (200, "application/xml", "<notice/>", {}),
    })

    resultado = ColectorTedFullNotices(cliente=cliente, repositorio=repo).enriquecer([
        _search_doc("fail-2026", 1),
        _search_doc("ok-2026", 2),
    ])

    assert resultado.accepted == 1
    assert resultado.failed == 1
    assert repo.contar_documentos_raw(source="ted_full_notice") == 1
