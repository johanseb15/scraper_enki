import json
from dataclasses import dataclass, field
from typing import Any

from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import DocumentoRaw, RegistroAwardUSASpendingObservado

UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RechazoAwardUSASpending:
    raw_document_id: int | None
    source_record_id: str
    reason: str


@dataclass(frozen=True)
class ResultadoExtraccionUSASpending:
    processed: int = 0
    extracted: int = 0
    partial: int = 0
    rejected: int = 0
    duplicate: int = 0
    rejected_records: list[RechazoAwardUSASpending] = field(default_factory=list)


class ExtractorUSASpendingAwards:
    def __init__(self, extractor_version: str = "usaspending_award_v1"):
        self.extractor_version = extractor_version

    def extraer_uno(self, documento: DocumentoRaw) -> RegistroAwardUSASpendingObservado:
        if documento.storage_id is None:
            raise ValueError("missing raw document storage id")
        try:
            raw = json.loads(documento.raw_content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid raw JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError("raw content must be a JSON object")

        source_record_id = self._pick(raw, "generated_internal_id", "internal_id")
        if source_record_id == UNKNOWN:
            raise ValueError("missing stable award identity")

        return RegistroAwardUSASpendingObservado(
            raw_document_id=documento.storage_id,
            source=documento.source,
            source_record_id=str(source_record_id),
            source_url=documento.source_url,
            extractor_version=self.extractor_version,
            extraction_status="EXTRACTED",
            recipient_raw=self._pick(raw, "Recipient Name"),
            recipient_uei_raw=self._pick(raw, "Recipient UEI"),
            awarding_agency_raw=self._pick(raw, "Awarding Agency"),
            awarding_sub_agency_raw=self._pick(raw, "Awarding Sub Agency"),
            funding_agency_raw=self._pick(raw, "Funding Agency"),
            funding_sub_agency_raw=self._pick(raw, "Funding Sub Agency"),
            description_raw=self._pick(raw, "Description", "Contract Description"),
            award_amount_raw=self._pick(raw, "Award Amount"),
            potential_award_amount_raw=self._pick(raw, "Potential Award Amount"),
            currency_raw="USD",
            naics_raw=self._pick(raw, "NAICS"),
            psc_raw=self._pick(raw, "PSC"),
            award_type_raw=self._pick(raw, "Contract Award Type"),
            start_date_raw=self._pick(raw, "Start Date"),
            end_date_raw=self._pick(raw, "End Date"),
            award_date_raw=self._pick(raw, "Award Date"),
            place_of_performance_raw={
                "state": self._pick(raw, "Place of Performance State Code"),
                "country": self._pick(raw, "Place of Performance Country Code"),
            },
            recipient_location_raw={
                "state": self._pick(raw, "Recipient State Code"),
                "country": self._pick(raw, "Recipient Country Code"),
                "raw": self._pick(raw, "Recipient Location"),
            },
            metadata={
                "award_id_raw": self._pick(raw, "Award ID"),
                "internal_id_raw": self._pick(raw, "internal_id"),
                "agency_slug_raw": self._pick(raw, "agency_slug"),
                "awarding_agency_id_raw": self._pick(raw, "awarding_agency_id"),
                "value_semantics": "award_amount",
                "query_bias": "NAICS 541511/541512/541513/541519 contracts, sorted by Award Amount desc",
            },
        )

    def extraer_lote(
        self,
        documentos: list[DocumentoRaw],
        repositorio: RepositorioEvidencia,
    ) -> ResultadoExtraccionUSASpending:
        extracted = 0
        partial = 0
        duplicate = 0
        rejected_records: list[RechazoAwardUSASpending] = []
        for documento in documentos:
            try:
                observacion = self.extraer_uno(documento)
            except ValueError as exc:
                rejected_records.append(
                    RechazoAwardUSASpending(
                        raw_document_id=documento.storage_id,
                        source_record_id=documento.source_record_id,
                        reason=str(exc),
                    )
                )
                continue
            if repositorio.guardar_observacion_usaspending_award(observacion):
                if observacion.extraction_status == "PARTIAL":
                    partial += 1
                else:
                    extracted += 1
            else:
                duplicate += 1
        return ResultadoExtraccionUSASpending(
            processed=len(documentos),
            extracted=extracted,
            partial=partial,
            rejected=len(rejected_records),
            duplicate=duplicate,
            rejected_records=rejected_records,
        )

    @staticmethod
    def _pick(raw: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = raw.get(key)
            if value not in (None, "", [], {}):
                return value
        return UNKNOWN
