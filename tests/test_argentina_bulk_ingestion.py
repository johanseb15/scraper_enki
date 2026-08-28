import base64
from datetime import datetime, timezone

from src.aplicacion.colector_argentina_bulk import (
    ColectorArgentinaBulk,
    RecursoArgentinaBulk,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


class ClienteBulkFake:
    def __init__(self, payloads):
        self.payloads = payloads

    def descargar(self, recurso: RecursoArgentinaBulk) -> tuple[bytes, dict[str, str]]:
        return self.payloads[recurso.resource_id], {"content-type": "text/csv", "content-length": str(len(self.payloads[recurso.resource_id]))}


def _resource(resource_id="res-1", name="Adjudicaciones 2026"):
    return RecursoArgentinaBulk(
        resource_id=resource_id,
        name=name,
        url=f"https://datos.gob.ar/{resource_id}.csv",
        resource_type="adjudicaciones",
        value_class="P0_ECONOMIC",
        metadata={"official": True},
    )


def _csv(text: str) -> bytes:
    return text.encode("utf-8-sig")


def test_bulk_csv_real_shaped_preserva_raw_document(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    content = _csv("""Numero_Proceso,Descripcion_SAF,CUIT,Descripcion_Proveedor,Documento_Contractual,Monto,Moneda,Fecha_de_Adjudicacion,Rubros
1,Buyer,20,Supplier,OC-1,10.00,Peso Argentino,01/01/2026 01:00:00 p.m.,INFORMATICA;
""")

    result = ColectorArgentinaBulk(
        ClienteBulkFake({"res-1": content}), repo, reloj=lambda: datetime(2026, 8, 11, tzinfo=timezone.utc)
    ).colectar([_resource()])

    assert result.files_downloaded == 1
    assert result.rows_accepted == 1
    doc = repo.listar_documentos_raw(source="datos_argentina_comprar")[0]
    assert doc.source_record_id == "res-1"
    assert doc.metadata["content_transfer_encoding"] == "base64"
    assert base64.b64decode(doc.raw_content.encode("ascii")) == content


def test_same_csv_twice_duplicate(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    content = _csv("""Numero_Proceso,Documento_Contractual
1,OC-1
""")
    collector = ColectorArgentinaBulk(ClienteBulkFake({"res-1": content}), repo)

    collector.colectar([_resource()])
    result = collector.colectar([_resource()])

    assert result.duplicates == 1
    assert repo.contar_documentos_raw(source="datos_argentina_comprar") == 1
    assert repo.contar_filas_argentina() == 1


def test_csv_changed_preserves_revision(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    first = _csv("""Numero_Proceso,Documento_Contractual
1,OC-1
""")
    second = _csv("""Numero_Proceso,Documento_Contractual
1,OC-2
""")

    ColectorArgentinaBulk(ClienteBulkFake({"res-1": first}), repo).colectar([_resource()])
    result = ColectorArgentinaBulk(ClienteBulkFake({"res-1": second}), repo).colectar([_resource()])

    assert result.files_downloaded == 1
    assert repo.contar_documentos_raw(source="datos_argentina_comprar") == 2


def test_malformed_row_rejected_batch_continues(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    content = _csv("""Numero_Proceso,Documento_Contractual
1,OC-1,EXTRA
2,OC-2
""")

    result = ColectorArgentinaBulk(ClienteBulkFake({"res-1": content}), repo).colectar([_resource()])

    assert result.rows_seen == 2
    assert result.rows_accepted == 1
    assert result.rows_rejected == 1
    assert repo.contar_filas_argentina() == 1


def test_schema_variant_by_year_does_not_shift_columns(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    old = RecursoArgentinaBulk("old", "Convocatorias 2016", "https://datos.gob.ar/old.csv", "convocatorias", "P1_MARKET_ACTIVITY", {})
    new = RecursoArgentinaBulk("new", "Convocatorias 2026", "https://datos.gob.ar/new.csv", "convocatorias", "P1_MARKET_ACTIVITY", {})
    payloads = {
        "old": _csv("""Numero_Proceso,Objeto_del_Proceso
1,Old object
"""),
        "new": _csv("""Numero_Proceso,Nro_SAF,Objeto_del_Proceso,Monto_Estimado
2,301,New object,100.00
"""),
    }

    result = ColectorArgentinaBulk(ClienteBulkFake(payloads), repo).colectar([old, new])
    rows = repo.listar_filas_argentina()

    assert result.files_downloaded == 2
    assert result.rows_accepted == 2
    assert rows[0].row_raw == {"Numero_Proceso": "1", "Objeto_del_Proceso": "Old object"}
    assert rows[1].row_raw["Monto_Estimado"] == "100.00"



class ClienteBulkPartialFailure:
    def __init__(self, good_payload):
        self.good_payload = good_payload

    def descargar(
        self,
        recurso: RecursoArgentinaBulk,
    ) -> tuple[bytes, dict[str, str]]:
        if recurso.resource_id == "bad":
            raise TimeoutError(
                "download timeout Authorization: Bearer argentina-secret"
            )

        return self.good_payload, {
            "content-type": "text/csv",
            "content-length": str(len(self.good_payload)),
        }


def test_bulk_operational_failure_preserves_diagnostic_and_batch_continues(
    tmp_path,
):
    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    good_payload = _csv(
        "Numero_Proceso,Documento_Contractual\n"
        "1,OC-1\n"
    )

    bad = _resource(
        resource_id="bad",
        name="Broken resource",
    )
    good = _resource(
        resource_id="good",
        name="Working resource",
    )

    result = ColectorArgentinaBulk(
        ClienteBulkPartialFailure(good_payload),
        repo,
    ).colectar([bad, good])

    assert result.failed == 1
    assert result.files_downloaded == 1
    assert result.rows_accepted == 1
    assert len(result.failures) == 1

    failure = result.failures[0]
    assert failure.source == "datos_argentina_comprar"
    assert failure.operation == "download_resource"
    assert failure.resource_id == "bad"
    assert failure.category.value == "NETWORK"
    assert failure.retryable is True
    assert failure.exception_type == "TimeoutError"
    assert "argentina-secret" not in failure.message_redacted



class ClienteBulkInvalidSchema:
    def descargar(
        self,
        recurso: RecursoArgentinaBulk,
    ) -> tuple[bytes, dict[str, str]]:
        return b"", {
            "content-type": "text/csv",
        }


def test_bulk_prepare_failure_has_precise_operation_not_download(tmp_path):
    repo = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    result = ColectorArgentinaBulk(
        ClienteBulkInvalidSchema(),
        repo,
    ).colectar([_resource(resource_id="invalid")])

    assert result.failed == 1
    assert len(result.failures) == 1

    failure = result.failures[0]
    assert failure.source == "datos_argentina_comprar"
    assert failure.operation == "prepare_raw_document"
    assert failure.resource_id == "invalid"
    assert failure.category.value == "PARSE"
    assert failure.retryable is False


class RepositorioBulkFailFirstPersistence:
    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = 0

    def guardar_documento_raw(self, documento):
        self.calls += 1

        if self.calls == 1:
            raise OSError(
                "db unavailable cookie=bulk-persistence-secret"
            )

        return self.delegate.guardar_documento_raw(documento)

    def __getattr__(self, name):
        return getattr(self.delegate, name)


def test_bulk_raw_persistence_failure_is_typed_and_next_resource_continues(
    tmp_path,
):
    delegate = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )
    repo = RepositorioBulkFailFirstPersistence(delegate)

    content = _csv(
        "Numero_Proceso,Documento_Contractual\n"
        "1,OC-1\n"
    )

    client = ClienteBulkFake({
        "first": content,
        "second": content,
    })

    first = _resource(
        resource_id="first",
        name="First",
    )
    second = _resource(
        resource_id="second",
        name="Second",
    )

    result = ColectorArgentinaBulk(
        client,
        repo,
    ).colectar([first, second])

    assert result.failed == 1
    assert result.files_downloaded == 1
    assert result.rows_accepted == 1
    assert len(result.failures) == 1

    failure = result.failures[0]
    assert failure.operation == "persist_raw_document"
    assert failure.resource_id == "first"
    assert failure.category.value == "PERSISTENCE"
    assert failure.retryable is False
    assert "bulk-persistence-secret" not in failure.message_redacted



class RepositorioBulkFailRowCount:
    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def contar_filas_argentina(self, *, raw_document_id=None):
        raise OSError(
            "row count failed token=row-count-secret"
        )


def test_bulk_duplicate_row_count_failure_is_typed(tmp_path):
    delegate = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )

    content = _csv(
        "Numero_Proceso,Documento_Contractual\n"
        "1,OC-1\n"
    )

    resource = _resource(
        resource_id="dup",
        name="Duplicate",
    )

    ColectorArgentinaBulk(
        ClienteBulkFake({"dup": content}),
        delegate,
    ).colectar([resource])

    repo = RepositorioBulkFailRowCount(delegate)

    result = ColectorArgentinaBulk(
        ClienteBulkFake({"dup": content}),
        repo,
    ).colectar([resource])

    assert result.failed == 1
    assert len(result.failures) == 1

    failure = result.failures[0]
    assert failure.operation == "inspect_persisted_rows"
    assert failure.resource_id == "dup"
    assert failure.category.value == "PERSISTENCE"
    assert failure.retryable is False
    assert "row-count-secret" not in failure.message_redacted


class RepositorioBulkFailRowsPersistence:
    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def guardar_filas_argentina(self, rows):
        raise OSError(
            "rows write failed api_key=rows-secret"
        )


def test_bulk_extracted_rows_persistence_failure_is_typed(tmp_path):
    delegate = RepositorioSQLiteEvidencia(
        str(tmp_path / "evidence.db")
    )
    repo = RepositorioBulkFailRowsPersistence(delegate)

    content = _csv(
        "Numero_Proceso,Documento_Contractual\n"
        "1,OC-1\n"
    )

    result = ColectorArgentinaBulk(
        ClienteBulkFake({"rows": content}),
        repo,
    ).colectar([
        _resource(
            resource_id="rows",
            name="Rows",
        )
    ])

    assert result.failed == 1
    assert result.files_downloaded == 1
    assert len(result.failures) == 1

    failure = result.failures[0]
    assert failure.operation == "persist_extracted_rows"
    assert failure.resource_id == "rows"
    assert failure.category.value == "PERSISTENCE"
    assert failure.retryable is False
    assert "rows-secret" not in failure.message_redacted
