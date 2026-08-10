import json
from dataclasses import dataclass, field
from typing import Any

from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import DocumentoRaw, RegistroContratacionObservado

UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RechazoExtraccion:
    raw_document_id: int | None
    source_record_id: str
    reason: str


@dataclass(frozen=True)
class ResultadoExtraccion:
    processed: int = 0
    extracted: int = 0
    partial: int = 0
    rejected: int = 0
    duplicate: int = 0
    rejected_records: list[RechazoExtraccion] = field(default_factory=list)


class ExtractorContratacionesTed:
    def __init__(self, extractor_version: str = "ted-procurement-v1"):
        self.extractor_version = extractor_version

    def extraer_uno(self, documento: DocumentoRaw) -> RegistroContratacionObservado:
        raw_document_id = self._raw_document_id(documento)
        try:
            raw = json.loads(documento.raw_content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid raw JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError("raw content must be a JSON object")

        source_record_id = self._pick(raw, "publication-number", "id")
        if source_record_id == UNKNOWN:
            raise ValueError("missing publication number")

        title_raw = raw.get("notice-title", UNKNOWN)
        classification_raw = raw.get("classification-cpv", UNKNOWN)
        buyer_raw = raw.get("buyer-name", UNKNOWN)
        country_raw = raw.get("buyer-country", UNKNOWN)
        published_at_raw = raw.get("publication-date", UNKNOWN)
        description_raw = raw.get("description-lot", UNKNOWN)
        supplier_raw = self._first_present(
            raw,
            [
                "tendering-party-name",
                "winner-name",
                "organisation-name-tenderer",
                "supplier-name",
            ],
        )
        value_raw, currency_raw, value_semantics = self._extract_value(raw)
        status = self._status(
            title_raw=title_raw,
            classification_raw=classification_raw,
            buyer_raw=buyer_raw,
            country_raw=country_raw,
            published_at_raw=published_at_raw,
        )

        return RegistroContratacionObservado(
            raw_document_id=raw_document_id,
            source=documento.source,
            source_record_id=str(source_record_id),
            source_url=documento.source_url,
            extractor_version=self.extractor_version,
            extraction_status=status,
            title_raw=title_raw,
            description_raw=description_raw,
            buyer_raw=buyer_raw,
            supplier_raw=supplier_raw,
            classification_raw=classification_raw,
            country_raw=country_raw,
            published_at_raw=published_at_raw,
            value_raw=value_raw,
            currency_raw=currency_raw,
            value_semantics=value_semantics,
            metadata={
                "notice_type_raw": raw.get("notice-type", UNKNOWN),
                "procedure_type_raw": raw.get("procedure-type", UNKNOWN),
                "links_raw": raw.get("links", UNKNOWN),
                "value_fields_raw": self._value_fields(raw),
            },
        )

    def extraer_lote(
        self,
        documentos: list[DocumentoRaw],
        repositorio: RepositorioEvidencia,
    ) -> ResultadoExtraccion:
        extracted = 0
        partial = 0
        duplicate = 0
        rejected_records: list[RechazoExtraccion] = []
        for documento in documentos:
            try:
                observacion = self.extraer_uno(documento)
            except ValueError as exc:
                rejected_records.append(
                    RechazoExtraccion(
                        raw_document_id=documento.storage_id,
                        source_record_id=documento.source_record_id,
                        reason=str(exc),
                    )
                )
                continue

            if repositorio.guardar_observacion_contratacion(observacion):
                if observacion.extraction_status == "PARTIAL":
                    partial += 1
                else:
                    extracted += 1
            else:
                duplicate += 1

        return ResultadoExtraccion(
            processed=len(documentos),
            extracted=extracted,
            partial=partial,
            rejected=len(rejected_records),
            duplicate=duplicate,
            rejected_records=rejected_records,
        )

    @staticmethod
    def _raw_document_id(documento: DocumentoRaw) -> int:
        if documento.storage_id is None:
            raise ValueError("missing raw document storage id")
        return documento.storage_id

    @staticmethod
    def _pick(raw: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = raw.get(key)
            if value not in (None, "", [], {}):
                return value
        return UNKNOWN

    @classmethod
    def _first_present(cls, raw: dict[str, Any], keys: list[str]) -> Any:
        return cls._pick(raw, *keys)

    @classmethod
    def _extract_value(cls, raw: dict[str, Any]) -> tuple[Any, Any, str]:
        candidates = [
            ("estimated_value", ["estimated-value-notice", "estimated-value-lot"]),
            (
                "award_value",
                ["result-awarded-value-lot", "result-final-value-notice", "awarded-value"],
            ),
            ("contract_value", ["contract-value", "contract-value-notice"]),
            (
                "framework_value",
                ["result-framework-maximum-value-cur-notice", "framework-value"],
            ),
        ]
        for semantics, keys in candidates:
            value = cls._pick(raw, *keys)
            if value != UNKNOWN:
                return value, cls._currency_for(raw, keys), semantics
        return UNKNOWN, cls._currency_for(raw, []), "unknown_value_semantics"

    @staticmethod
    def _currency_for(raw: dict[str, Any], value_keys: list[str]) -> Any:
        currency_keys = []
        for key in value_keys:
            currency_keys.extend([f"{key}-currency", key.replace("value", "value-cur")])
        currency_keys.extend(
            [
                "currency",
                "value-currency",
                "estimated-value-notice-currency",
                "result-awarded-value-lot-currency",
                "result-final-value-notice-currency",
                "result-framework-maximum-value-cur-notice",
            ]
        )
        for key in currency_keys:
            value = raw.get(key)
            if value not in (None, "", [], {}):
                return value
        return UNKNOWN

    @staticmethod
    def _value_fields(raw: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in raw.items()
            if "value" in key.lower()
            or "currency" in key.lower()
            or "amount" in key.lower()
        }

    @staticmethod
    def _status(**core_fields: Any) -> str:
        missing = [key for key, value in core_fields.items() if value == UNKNOWN]
        return "PARTIAL" if missing else "EXTRACTED"
