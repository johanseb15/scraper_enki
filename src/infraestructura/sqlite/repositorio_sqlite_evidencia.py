import json
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any

from src.dominio.evidencia import (
    ConsultaUsuarioRaw,
    DocumentoRaw,
    FuenteCandidata,
    RegistroAwardUSASpendingObservado,
    RegistroContratacionObservado,
)


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
            conexion.execute("""
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
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_language_evidence_source_language
                ON language_evidence(source, language)
            """)
            conexion.execute("""
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
            """)
            conexion.execute("""
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
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_documents_source_record
                ON raw_documents(source, source_record_id)
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_documents_hash
                ON raw_documents(content_hash)
            """)
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS procurement_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_document_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    source_record_id TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    extractor_version TEXT NOT NULL,
                    extraction_status TEXT NOT NULL,
                    rejection_reason TEXT,
                    title_raw_json TEXT NOT NULL,
                    description_raw_json TEXT NOT NULL,
                    buyer_raw_json TEXT NOT NULL,
                    supplier_raw_json TEXT NOT NULL,
                    classification_raw_json TEXT NOT NULL,
                    country_raw_json TEXT NOT NULL,
                    published_at_raw_json TEXT NOT NULL,
                    value_raw_json TEXT NOT NULL,
                    currency_raw_json TEXT NOT NULL,
                    value_semantics TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    extracted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(raw_document_id, extractor_version)
                )
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_procurement_observations_source
                ON procurement_observations(source, source_record_id)
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_procurement_observations_status
                ON procurement_observations(extractor_version, extraction_status)
            """)
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS usaspending_award_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_document_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    source_record_id TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    extractor_version TEXT NOT NULL,
                    extraction_status TEXT NOT NULL,
                    rejection_reason TEXT,
                    recipient_raw_json TEXT NOT NULL,
                    recipient_uei_raw_json TEXT NOT NULL,
                    awarding_agency_raw_json TEXT NOT NULL,
                    awarding_sub_agency_raw_json TEXT NOT NULL,
                    funding_agency_raw_json TEXT NOT NULL,
                    funding_sub_agency_raw_json TEXT NOT NULL,
                    description_raw_json TEXT NOT NULL,
                    award_amount_raw_json TEXT NOT NULL,
                    potential_award_amount_raw_json TEXT NOT NULL,
                    currency_raw_json TEXT NOT NULL,
                    naics_raw_json TEXT NOT NULL,
                    psc_raw_json TEXT NOT NULL,
                    award_type_raw_json TEXT NOT NULL,
                    start_date_raw_json TEXT NOT NULL,
                    end_date_raw_json TEXT NOT NULL,
                    award_date_raw_json TEXT NOT NULL,
                    place_of_performance_raw_json TEXT NOT NULL,
                    recipient_location_raw_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    extracted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(raw_document_id, extractor_version)
                )
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_usaspending_awards_source
                ON usaspending_award_observations(source, source_record_id)
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_usaspending_awards_status
                ON usaspending_award_observations(extractor_version, extraction_status)
            """)

    def guardar_lenguaje(self, registro: ConsultaUsuarioRaw) -> bool:
        with closing(self._conectar()) as conexion, conexion:
            cursor = conexion.execute("""
                INSERT OR IGNORE INTO language_evidence (
                    source, source_id, source_url, raw_text, language,
                    observed_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (registro.source, registro.source_id, registro.source_url, registro.raw_text, registro.language, registro.observed_at.isoformat(), self._json(registro.metadata)))
            return cursor.rowcount == 1

    def guardar_fuente(self, fuente: FuenteCandidata) -> bool:
        with closing(self._conectar()) as conexion, conexion:
            cursor = conexion.execute("""
                INSERT OR IGNORE INTO source_registry (
                    name, url, source_type, country, language, status,
                    acquisition_method, last_checked_at, notes, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fuente.name, fuente.url, fuente.source_type, fuente.country, fuente.language, fuente.status, fuente.acquisition_method, fuente.last_checked_at.isoformat() if fuente.last_checked_at else None, fuente.notes, self._json(fuente.metadata)))
            return cursor.rowcount == 1

    def guardar_documento_raw(self, documento: DocumentoRaw) -> bool:
        with closing(self._conectar()) as conexion, conexion:
            cursor = conexion.execute("""
                INSERT OR IGNORE INTO raw_documents (
                    source, source_record_id, source_url, retrieved_at,
                    content_type, raw_content, content_hash, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (documento.source, documento.source_record_id, documento.source_url, documento.retrieved_at.isoformat(), documento.content_type, documento.raw_content, documento.content_hash, self._json(documento.metadata)))
            return cursor.rowcount == 1

    def guardar_observacion_contratacion(self, observacion: RegistroContratacionObservado) -> bool:
        with closing(self._conectar()) as conexion, conexion:
            cursor = conexion.execute("""
                INSERT OR IGNORE INTO procurement_observations (
                    raw_document_id, source, source_record_id, source_url,
                    extractor_version, extraction_status, rejection_reason,
                    title_raw_json, description_raw_json, buyer_raw_json,
                    supplier_raw_json, classification_raw_json, country_raw_json,
                    published_at_raw_json, value_raw_json, currency_raw_json,
                    value_semantics, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (observacion.raw_document_id, observacion.source, observacion.source_record_id, observacion.source_url, observacion.extractor_version, observacion.extraction_status, observacion.rejection_reason, self._json(observacion.title_raw), self._json(observacion.description_raw), self._json(observacion.buyer_raw), self._json(observacion.supplier_raw), self._json(observacion.classification_raw), self._json(observacion.country_raw), self._json(observacion.published_at_raw), self._json(observacion.value_raw), self._json(observacion.currency_raw), observacion.value_semantics, self._json(observacion.metadata)))
            return cursor.rowcount == 1

    def guardar_observacion_usaspending_award(self, observacion: RegistroAwardUSASpendingObservado) -> bool:
        with closing(self._conectar()) as conexion, conexion:
            cursor = conexion.execute("""
                INSERT OR IGNORE INTO usaspending_award_observations (
                    raw_document_id, source, source_record_id, source_url,
                    extractor_version, extraction_status, rejection_reason,
                    recipient_raw_json, recipient_uei_raw_json,
                    awarding_agency_raw_json, awarding_sub_agency_raw_json,
                    funding_agency_raw_json, funding_sub_agency_raw_json,
                    description_raw_json, award_amount_raw_json,
                    potential_award_amount_raw_json, currency_raw_json,
                    naics_raw_json, psc_raw_json, award_type_raw_json,
                    start_date_raw_json, end_date_raw_json, award_date_raw_json,
                    place_of_performance_raw_json, recipient_location_raw_json,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (observacion.raw_document_id, observacion.source, observacion.source_record_id, observacion.source_url, observacion.extractor_version, observacion.extraction_status, observacion.rejection_reason, self._json(observacion.recipient_raw), self._json(observacion.recipient_uei_raw), self._json(observacion.awarding_agency_raw), self._json(observacion.awarding_sub_agency_raw), self._json(observacion.funding_agency_raw), self._json(observacion.funding_sub_agency_raw), self._json(observacion.description_raw), self._json(observacion.award_amount_raw), self._json(observacion.potential_award_amount_raw), self._json(observacion.currency_raw), self._json(observacion.naics_raw), self._json(observacion.psc_raw), self._json(observacion.award_type_raw), self._json(observacion.start_date_raw), self._json(observacion.end_date_raw), self._json(observacion.award_date_raw), self._json(observacion.place_of_performance_raw), self._json(observacion.recipient_location_raw), self._json(observacion.metadata)))
            return cursor.rowcount == 1

    def contar_lenguaje(self, source: str | None = None, language: str | None = None) -> int:
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
            return int(conexion.execute("SELECT COUNT(*) AS total FROM source_registry").fetchone()["total"])

    def contar_documentos_raw(self, source: str | None = None) -> int:
        query = "SELECT COUNT(*) AS total FROM raw_documents"
        params: list[Any] = []
        if source:
            query += " WHERE source = ?"
            params.append(source)
        with closing(self._conectar()) as conexion:
            return int(conexion.execute(query, params).fetchone()["total"])

    def contar_observaciones_contratacion(self, extractor_version: str | None = None, extraction_status: str | None = None) -> int:
        return self._contar_observaciones("procurement_observations", extractor_version, extraction_status)

    def contar_observaciones_usaspending_awards(self, extractor_version: str | None = None, extraction_status: str | None = None) -> int:
        return self._contar_observaciones("usaspending_award_observations", extractor_version, extraction_status)

    def _contar_observaciones(self, table: str, extractor_version: str | None, extraction_status: str | None) -> int:
        query = f"SELECT COUNT(*) AS total FROM {table}"
        params: list[Any] = []
        filters = []
        if extractor_version:
            filters.append("extractor_version = ?")
            params.append(extractor_version)
        if extraction_status:
            filters.append("extraction_status = ?")
            params.append(extraction_status)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        with closing(self._conectar()) as conexion:
            return int(conexion.execute(query, params).fetchone()["total"])

    def listar_lenguaje(self, source: str | None = None, language: str | None = None) -> list[ConsultaUsuarioRaw]:
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

    def listar_documentos_raw(self, source: str | None = None, limit: int | None = None) -> list[DocumentoRaw]:
        query = "SELECT * FROM raw_documents"
        params: list[Any] = []
        if source:
            query += " WHERE source = ?"
            params.append(source)
        query += " ORDER BY id"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with closing(self._conectar()) as conexion:
            rows = conexion.execute(query, params).fetchall()
        return [self._row_to_documento_raw(row) for row in rows]

    def listar_observaciones_contratacion(self, extractor_version: str | None = None, limit: int | None = None) -> list[RegistroContratacionObservado]:
        query = "SELECT * FROM procurement_observations"
        params: list[Any] = []
        if extractor_version:
            query += " WHERE extractor_version = ?"
            params.append(extractor_version)
        query += " ORDER BY id"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with closing(self._conectar()) as conexion:
            rows = conexion.execute(query, params).fetchall()
        return [self._row_to_observacion(row) for row in rows]

    def listar_observaciones_usaspending_awards(self, extractor_version: str | None = None, limit: int | None = None) -> list[RegistroAwardUSASpendingObservado]:
        query = "SELECT * FROM usaspending_award_observations"
        params: list[Any] = []
        if extractor_version:
            query += " WHERE extractor_version = ?"
            params.append(extractor_version)
        query += " ORDER BY id"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with closing(self._conectar()) as conexion:
            rows = conexion.execute(query, params).fetchall()
        return [self._row_to_usaspending_award(row) for row in rows]

    @staticmethod
    def _row_to_lenguaje(row: sqlite3.Row) -> ConsultaUsuarioRaw:
        return ConsultaUsuarioRaw(source=row["source"], source_id=row["source_id"], source_url=row["source_url"], raw_text=row["raw_text"], language=row["language"], observed_at=datetime.fromisoformat(row["observed_at"]), metadata=json.loads(row["metadata_json"]))

    @staticmethod
    def _row_to_fuente(row: sqlite3.Row) -> FuenteCandidata:
        return FuenteCandidata(name=row["name"], url=row["url"], source_type=row["source_type"], country=row["country"] or "", language=row["language"] or "", status=row["status"], acquisition_method=row["acquisition_method"], last_checked_at=(datetime.fromisoformat(row["last_checked_at"]) if row["last_checked_at"] else None), notes=row["notes"] or "", metadata=json.loads(row["metadata_json"]))

    @staticmethod
    def _row_to_documento_raw(row: sqlite3.Row) -> DocumentoRaw:
        return DocumentoRaw(source=row["source"], source_record_id=row["source_record_id"], source_url=row["source_url"], retrieved_at=datetime.fromisoformat(row["retrieved_at"]), content_type=row["content_type"], raw_content=row["raw_content"], content_hash=row["content_hash"], metadata=json.loads(row["metadata_json"]), storage_id=int(row["id"]))

    @classmethod
    def _row_to_observacion(cls, row: sqlite3.Row) -> RegistroContratacionObservado:
        return RegistroContratacionObservado(raw_document_id=int(row["raw_document_id"]), source=row["source"], source_record_id=row["source_record_id"], source_url=row["source_url"], extractor_version=row["extractor_version"], extraction_status=row["extraction_status"], rejection_reason=row["rejection_reason"] or "", title_raw=cls._loads(row["title_raw_json"]), description_raw=cls._loads(row["description_raw_json"]), buyer_raw=cls._loads(row["buyer_raw_json"]), supplier_raw=cls._loads(row["supplier_raw_json"]), classification_raw=cls._loads(row["classification_raw_json"]), country_raw=cls._loads(row["country_raw_json"]), published_at_raw=cls._loads(row["published_at_raw_json"]), value_raw=cls._loads(row["value_raw_json"]), currency_raw=cls._loads(row["currency_raw_json"]), value_semantics=row["value_semantics"], metadata=cls._loads(row["metadata_json"]))

    @classmethod
    def _row_to_usaspending_award(cls, row: sqlite3.Row) -> RegistroAwardUSASpendingObservado:
        return RegistroAwardUSASpendingObservado(raw_document_id=int(row["raw_document_id"]), source=row["source"], source_record_id=row["source_record_id"], source_url=row["source_url"], extractor_version=row["extractor_version"], extraction_status=row["extraction_status"], rejection_reason=row["rejection_reason"] or "", recipient_raw=cls._loads(row["recipient_raw_json"]), recipient_uei_raw=cls._loads(row["recipient_uei_raw_json"]), awarding_agency_raw=cls._loads(row["awarding_agency_raw_json"]), awarding_sub_agency_raw=cls._loads(row["awarding_sub_agency_raw_json"]), funding_agency_raw=cls._loads(row["funding_agency_raw_json"]), funding_sub_agency_raw=cls._loads(row["funding_sub_agency_raw_json"]), description_raw=cls._loads(row["description_raw_json"]), award_amount_raw=cls._loads(row["award_amount_raw_json"]), potential_award_amount_raw=cls._loads(row["potential_award_amount_raw_json"]), currency_raw=cls._loads(row["currency_raw_json"]), naics_raw=cls._loads(row["naics_raw_json"]), psc_raw=cls._loads(row["psc_raw_json"]), award_type_raw=cls._loads(row["award_type_raw_json"]), start_date_raw=cls._loads(row["start_date_raw_json"]), end_date_raw=cls._loads(row["end_date_raw_json"]), award_date_raw=cls._loads(row["award_date_raw_json"]), place_of_performance_raw=cls._loads(row["place_of_performance_raw_json"]), recipient_location_raw=cls._loads(row["recipient_location_raw_json"]), metadata=cls._loads(row["metadata_json"]))

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _loads(value: str) -> Any:
        return json.loads(value)
