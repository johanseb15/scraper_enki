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


@dataclass(frozen=True)
class RegistroAwardUSASpendingObservado:
    raw_document_id: int
    source: str
    source_record_id: str
    source_url: str
    extractor_version: str
    extraction_status: str
    recipient_raw: Any
    recipient_uei_raw: Any
    awarding_agency_raw: Any
    awarding_sub_agency_raw: Any
    funding_agency_raw: Any
    funding_sub_agency_raw: Any
    description_raw: Any
    award_amount_raw: Any
    potential_award_amount_raw: Any
    currency_raw: Any
    naics_raw: Any
    psc_raw: Any
    award_type_raw: Any
    start_date_raw: Any
    end_date_raw: Any
    award_date_raw: Any
    place_of_performance_raw: Any
    recipient_location_raw: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    rejection_reason: str = ""


@dataclass(frozen=True)
class RegistroOrdenCompraMercadoPublicoObservada:
    raw_document_id: int
    source: str
    source_record_id: str
    source_url: str
    extractor_version: str
    extraction_status: str
    order_code_raw: Any
    name_raw: Any
    description_raw: Any
    buyer_raw: Any
    supplier_raw: Any
    status_raw: Any
    date_raw: Any
    currency_raw: Any
    order_total_raw: Any
    location_raw: Any
    items_count_raw: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    rejection_reason: str = ""
    storage_id: int | None = None


@dataclass(frozen=True)
class RegistroLineaOrdenCompraMercadoPublicoObservada:
    raw_document_id: int
    source: str
    source_record_id: str
    source_url: str
    extractor_version: str
    extraction_status: str
    order_source_record_id: str
    order_observation_id: int | None
    line_index: int
    item_stable_id_raw: Any
    description_raw: Any
    category_raw: Any
    category_code_raw: Any
    product_code_raw: Any
    quantity_raw: Any
    unit_raw: Any
    net_price_raw: Any
    total_raw: Any
    currency_raw: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    rejection_reason: str = ""
    storage_id: int | None = None


@dataclass(frozen=True)
class RegistroFilaArgentinaObservada:
    raw_document_id: int
    source: str
    source_record_id: str
    source_url: str
    extractor_version: str
    extraction_status: str
    resource_id: str
    resource_name: str
    resource_type: str
    row_number: int
    stable_id_raw: Any
    row_raw: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    rejection_reason: str = ""
    storage_id: int | None = None


@dataclass(frozen=True)
class RegistroPrecioComercialObservado:
    raw_document_id: int
    source: str
    source_record_id: str
    source_url: str
    extractor_version: str
    extraction_status: str
    provider_raw: Any
    economic_object_raw: Any
    scope_raw: Any
    price_raw: Any
    price_value: Any
    currency_raw: Any
    device_type_raw: Any
    operating_system_raw: Any
    backup_raw: Any
    drivers_raw: Any
    programs_raw: Any
    license_raw: Any
    modality_raw: Any
    comparable_status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    rejection_reason: str = ""
    storage_id: int | None = None
