from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ConsultaUsuarioRaw:
    source: str
    source_id: str
    source_url: str
    raw_text: str
    language: str
    observed_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FuenteCandidata:
    name: str
    url: str
    source_type: str
    country: str
    language: str
    acquisition_method: str
    status: str = "CANDIDATE"
    last_checked_at: datetime | None = None
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentoRaw:
    source: str
    source_record_id: str
    source_url: str
    retrieved_at: datetime
    content_type: str
    raw_content: str
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
    storage_id: int | None = None


@dataclass(frozen=True)
class RegistroContratacionObservado:
    raw_document_id: int
    source: str
    source_record_id: str
    source_url: str
    extractor_version: str
    extraction_status: str
    title_raw: Any
    description_raw: Any
    buyer_raw: Any
    supplier_raw: Any
    classification_raw: Any
    country_raw: Any
    published_at_raw: Any
    value_raw: Any
    currency_raw: Any
    value_semantics: str
    metadata: dict[str, Any] = field(default_factory=dict)
    rejection_reason: str = ""
