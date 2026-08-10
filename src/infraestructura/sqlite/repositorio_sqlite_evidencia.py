import json
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any

from src.dominio.evidencia import ConsultaUsuarioRaw, DocumentoRaw, FuenteCandidata


class RepositorioSQLiteEvidencia:
    """Persistencia SQLite para evidencia no economica."""

    def __init__(self, ruta_db: str = "datos.db"):
        self.ruta_db = ruta_db
        self._crear_tablas()

    def _conectar(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.ruta_db)
        conexion.row_factory = sqlite3.Row
        return conexion

    def _crear_tablas(self) -> None:
        with closing(self._conectar()) as conexion, conexion:
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS language_evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    language TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, source_id)
                )
                """
            )
            conexion.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_language_evidence_source_language
                ON language_evidence(source, language)
                """
            )
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS source_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    country TEXT,
                    language TEXT,
                    status TEXT NOT NULL,
                    acquisition_method TEXT NOT NULL,
                    last_checked_at TEXT,
                    notes TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(url, source_type)
                )
                """
            )
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS raw_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_record_id TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    raw_content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, source_record_id, content_hash)
                )
                """
            )
            conexion.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_raw_documents_source_record
                ON raw_documents(source, source_record_id)
                """
            )
            conexion.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_raw_documents_hash
                ON raw_documents(content_hash)
                """
            )

    def guardar_lenguaje(self, registro: ConsultaUsuarioRaw) -> bool:
        with closing(self._conectar()) as conexion, conexion:
            cursor = conexion.execute(
                """
                INSERT OR IGNORE INTO language_evidence (
                    source,
                    source_id,
                    source_url,
                    raw_text,
                    language,
                    observed_at,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    registro.source,
                    registro.source_id,
                    registro.source_url,
                    registro.raw_text,
                    registro.language,
                    registro.observed_at.isoformat(),
                    json.dumps(registro.metadata, ensure_ascii=False, sort_keys=True),
                ),
            )
            return cursor.rowcount == 1

    def guardar_fuente(self, fuente: FuenteCandidata) -> bool:
        with closing(self._conectar()) as conexion, conexion:
            cursor = conexion.execute(
                """
                INSERT OR IGNORE INTO source_registry (
                    name,
                    url,
                    source_type,
                    country,
                    language,
                    status,
                    acquisition_method,
                    last_checked_at,
                    notes,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fuente.name,
                    fuente.url,
                    fuente.source_type,
                    fuente.country,
                    fuente.language,
                    fuente.status,
                    fuente.acquisition_method,
                    fuente.last_checked_at.isoformat() if fuente.last_checked_at else None,
                    fuente.notes,
                    json.dumps(fuente.metadata, ensure_ascii=False, sort_keys=True),
                ),
            )
            return cursor.rowcount == 1

    def guardar_documento_raw(self, documento: DocumentoRaw) -> bool:
        with closing(self._conectar()) as conexion, conexion:
            cursor = conexion.execute(
                """
                INSERT OR IGNORE INTO raw_documents (
                    source,
                    source_record_id,
                    source_url,
                    retrieved_at,
                    content_type,
                    raw_content,
                    content_hash,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    documento.source,
                    documento.source_record_id,
                    documento.source_url,
                    documento.retrieved_at.isoformat(),
                    documento.content_type,
                    documento.raw_content,
                    documento.content_hash,
                    json.dumps(documento.metadata, ensure_ascii=False, sort_keys=True),
                ),
            )
            return cursor.rowcount == 1

    def contar_lenguaje(
        self,
        source: str | None = None,
        language: str | None = None,
    ) -> int:
        query = "SELECT COUNT(*) AS total FROM language_evidence"
        params: list[Any] = []
        filters = []
        if source:
            filters.append("source = ?")
            params.append(source)
        if language:
            filters.append("language = ?")
            params.append(language)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        with closing(self._conectar()) as conexion:
            return int(conexion.execute(query, params).fetchone()["total"])

    def contar_fuentes(self) -> int:
        with closing(self._conectar()) as conexion:
            return int(
                conexion.execute("SELECT COUNT(*) AS total FROM source_registry").fetchone()[
                    "total"
                ]
            )

    def contar_documentos_raw(self, source: str | None = None) -> int:
        query = "SELECT COUNT(*) AS total FROM raw_documents"
        params: list[Any] = []
        if source:
            query += " WHERE source = ?"
            params.append(source)
        with closing(self._conectar()) as conexion:
            return int(conexion.execute(query, params).fetchone()["total"])

    def listar_lenguaje(
        self,
        source: str | None = None,
        language: str | None = None,
    ) -> list[ConsultaUsuarioRaw]:
        query = "SELECT * FROM language_evidence"
        params: list[Any] = []
        filters = []
        if source:
            filters.append("source = ?")
            params.append(source)
        if language:
            filters.append("language = ?")
            params.append(language)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY id"
        with closing(self._conectar()) as conexion:
            rows = conexion.execute(query, params).fetchall()
        return [self._row_to_lenguaje(row) for row in rows]

    def listar_fuentes(self) -> list[FuenteCandidata]:
        with closing(self._conectar()) as conexion:
            rows = conexion.execute("SELECT * FROM source_registry ORDER BY id").fetchall()
        return [self._row_to_fuente(row) for row in rows]

    def listar_documentos_raw(self, source: str | None = None) -> list[DocumentoRaw]:
        query = "SELECT * FROM raw_documents"
        params: list[Any] = []
        if source:
            query += " WHERE source = ?"
            params.append(source)
        query += " ORDER BY id"
        with closing(self._conectar()) as conexion:
            rows = conexion.execute(query, params).fetchall()
        return [self._row_to_documento_raw(row) for row in rows]

    @staticmethod
    def _row_to_lenguaje(row: sqlite3.Row) -> ConsultaUsuarioRaw:
        return ConsultaUsuarioRaw(
            source=row["source"],
            source_id=row["source_id"],
            source_url=row["source_url"],
            raw_text=row["raw_text"],
            language=row["language"],
            observed_at=datetime.fromisoformat(row["observed_at"]),
            metadata=json.loads(row["metadata_json"]),
        )

    @staticmethod
    def _row_to_fuente(row: sqlite3.Row) -> FuenteCandidata:
        return FuenteCandidata(
            name=row["name"],
            url=row["url"],
            source_type=row["source_type"],
            country=row["country"] or "",
            language=row["language"] or "",
            status=row["status"],
            acquisition_method=row["acquisition_method"],
            last_checked_at=(
                datetime.fromisoformat(row["last_checked_at"])
                if row["last_checked_at"]
                else None
            ),
            notes=row["notes"] or "",
            metadata=json.loads(row["metadata_json"]),
        )

    @staticmethod
    def _row_to_documento_raw(row: sqlite3.Row) -> DocumentoRaw:
        return DocumentoRaw(
            source=row["source"],
            source_record_id=row["source_record_id"],
            source_url=row["source_url"],
            retrieved_at=datetime.fromisoformat(row["retrieved_at"]),
            content_type=row["content_type"],
            raw_content=row["raw_content"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata_json"]),
        )
