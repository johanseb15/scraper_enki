import base64
import csv
import hashlib
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import DocumentoRaw, RegistroFilaArgentinaObservada

SOURCE = "datos_argentina_comprar"
EXTRACTOR_VERSION = "argentina_open_procurement_bulk_v1"


@dataclass(frozen=True)
class RecursoArgentinaBulk:
    resource_id: str
    name: str
    url: str
    resource_type: str
    value_class: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ClienteArgentinaBulk(Protocol):
    def descargar(self, recurso: RecursoArgentinaBulk) -> tuple[bytes, dict[str, str]]:
        """Descarga un recurso CSV oficial y devuelve bytes + headers HTTP."""


@dataclass(frozen=True)
class FilaArgentinaRechazada:
    resource_id: str
    row_number: int
    reason: str


@dataclass
class ResultadoArgentinaBulk:
    files_requested: int = 0
    files_downloaded: int = 0
    bytes_downloaded: int = 0
    duplicates: int = 0
    failed: int = 0
    rows_seen: int = 0
    rows_accepted: int = 0
    rows_rejected: int = 0
    rejected_rows: list[FilaArgentinaRechazada] = field(default_factory=list)


class ColectorArgentinaBulk:
    def __init__(
        self,
        cliente: ClienteArgentinaBulk,
        repositorio: RepositorioEvidencia,
        reloj=None,
        extractor_version: str = EXTRACTOR_VERSION,
    ):
        self.cliente = cliente
        self.repositorio = repositorio
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))
        self.extractor_version = extractor_version

    def colectar(self, recursos: list[RecursoArgentinaBulk]) -> ResultadoArgentinaBulk:
        resultado = ResultadoArgentinaBulk(files_requested=len(recursos))
        for recurso in recursos:
            try:
                payload, headers = self.cliente.descargar(recurso)
                documento, decoded = self._documento_raw(recurso, payload, headers)
            except Exception:
                resultado.failed += 1
                continue

            inserted = self.repositorio.guardar_documento_raw(documento)
            stored_doc = self._latest_raw_document(recurso.resource_id, documento.content_hash)
            if not inserted:
                resultado.duplicates += 1
                if self.repositorio.contar_filas_argentina(raw_document_id=stored_doc.storage_id) > 0:
                    continue
            else:
                resultado.files_downloaded += 1
                resultado.bytes_downloaded += len(payload)

            parse_result = self._parse_rows(recurso, stored_doc, decoded)
            resultado.rows_seen += parse_result.rows_seen
            resultado.rows_rejected += parse_result.rows_rejected
            resultado.rejected_rows.extend(parse_result.rejected_rows)
            resultado.rows_accepted += self.repositorio.guardar_filas_argentina(parse_result.rows)
        return resultado

    def _latest_raw_document(self, resource_id: str, content_hash: str) -> DocumentoRaw:
        for doc in self.repositorio.listar_documentos_raw(source=SOURCE):
            if doc.source_record_id == resource_id and doc.content_hash == content_hash:
                return doc
        raise RuntimeError("saved raw document not found")

    def _documento_raw(
        self,
        recurso: RecursoArgentinaBulk,
        payload: bytes,
        headers: dict[str, str],
    ) -> tuple[DocumentoRaw, str]:
        encoding, decoded = self._decode(payload)
        delimiter, csv_headers = self._sniff(decoded)
        content_hash = hashlib.sha256(payload).hexdigest()
        metadata = {
            "dataset_id": "sistema-de-contrataciones-electronicas",
            "resource_id": recurso.resource_id,
            "resource_name": recurso.name,
            "resource_type": recurso.resource_type,
            "value_class": recurso.value_class,
            "content_transfer_encoding": "base64",
            "original_sha256": content_hash,
            "encoding": encoding,
            "delimiter": delimiter,
            "headers": csv_headers,
            "http_headers": headers,
            **recurso.metadata,
        }
        return DocumentoRaw(
            source=SOURCE,
            source_record_id=recurso.resource_id,
            source_url=recurso.url,
            retrieved_at=self.reloj(),
            content_type=headers.get("content-type", "text/csv"),
            raw_content=base64.b64encode(payload).decode("ascii"),
            content_hash=content_hash,
            metadata=metadata,
        ), decoded

    def _parse_rows(
        self,
        recurso: RecursoArgentinaBulk,
        documento: DocumentoRaw,
        decoded: str,
    ) -> "ParseResult":
        reader = csv.DictReader(io.StringIO(decoded), delimiter=documento.metadata["delimiter"])
        rows: list[RegistroFilaArgentinaObservada] = []
        rejected: list[FilaArgentinaRechazada] = []
        seen = 0
        for row_number, row in enumerate(reader, start=2):
            if row is None:
                continue
            if not any((value or "").strip() for key, value in row.items() if key is not None):
                continue
            seen += 1
            if None in row:
                rejected.append(FilaArgentinaRechazada(recurso.resource_id, row_number, "extra columns beyond header"))
                continue
            clean_row = {str(key): (value if value is not None else "") for key, value in row.items()}
            stable_id = self._stable_id(recurso.resource_type, clean_row, row_number)
            if stable_id == "UNKNOWN":
                rejected.append(FilaArgentinaRechazada(recurso.resource_id, row_number, "missing stable row identity"))
                continue
            rows.append(
                RegistroFilaArgentinaObservada(
                    raw_document_id=documento.storage_id or 0,
                    source=SOURCE,
                    source_record_id=f"{recurso.resource_id}:ROW:{row_number}",
                    source_url=recurso.url,
                    extractor_version=self.extractor_version,
                    extraction_status="EXTRACTED",
                    resource_id=recurso.resource_id,
                    resource_name=recurso.name,
                    resource_type=recurso.resource_type,
                    row_number=row_number,
                    stable_id_raw=stable_id,
                    row_raw=clean_row,
                    metadata={
                        "value_class": recurso.value_class,
                        "schema_headers": documento.metadata["headers"],
                    },
                )
            )
        return ParseResult(rows_seen=seen, rows=rows, rows_rejected=len(rejected), rejected_rows=rejected)

    @staticmethod
    def _decode(payload: bytes) -> tuple[str, str]:
        for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            try:
                return encoding, payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("unsupported CSV encoding")

    @staticmethod
    def _sniff(decoded: str) -> tuple[str, list[str]]:
        sample = "\n".join(decoded.splitlines()[:20])
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;	|")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","
        reader = csv.reader(io.StringIO(decoded), delimiter=delimiter)
        headers = next(reader, [])
        if not headers:
            raise ValueError("CSV without headers")
        return delimiter, headers

    @staticmethod
    def _stable_id(resource_type: str, row: dict[str, str], row_number: int) -> str:
        if resource_type == "adjudicaciones":
            return "|".join([row.get("Numero_Proceso", ""), row.get("Documento_Contractual", ""), row.get("CUIT", "")]).strip("|") or "UNKNOWN"
        if resource_type == "convocatorias":
            return row.get("Numero_Proceso", "").strip() or "UNKNOWN"
        if resource_type == "sipro":
            return row.get("CUIT_NIT", "").strip() or "UNKNOWN"
        if resource_type == "sibys":
            return row.get("codigo", "").strip() or "UNKNOWN"
        return f"ROW:{row_number}"


@dataclass(frozen=True)
class ParseResult:
    rows_seen: int
    rows: list[RegistroFilaArgentinaObservada]
    rows_rejected: int
    rejected_rows: list[FilaArgentinaRechazada]
