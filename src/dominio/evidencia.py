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
