import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from src.aplicacion.acquisition_failure import (
    AcquisitionFailure,
    AcquisitionFailureCategory,
    acquisition_failure_from_exception,
)
from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import DocumentoRaw, FuenteCandidata

USASPENDING_QUERY = {
    "award_type_codes": ["A", "B", "C", "D"],
    "time_period": [{"start_date": "2024-01-01", "end_date": "2026-08-10"}],
    "naics_codes": ["541511", "541512", "541513", "541519"],
}


class ClienteUSASpending(Protocol):
    def buscar_awards(self, *, limit: int) -> list[dict[str, Any]]:
        """Devuelve awards raw desde la fuente externa."""


@dataclass(frozen=True)
class RegistroUSASpendingRechazado:
    index: int
    reason: str


@dataclass(frozen=True)
class ResultadoUSASpending:
    requested: int = 0
    downloaded: int = 0
    accepted: int = 0
    duplicate: int = 0
    rejected: int = 0
    failed: int = 0
    rejected_records: list[RegistroUSASpendingRechazado] = field(default_factory=list)
    failures: list[AcquisitionFailure] = field(default_factory=list)


class ColectorUSASpending:
    def __init__(
        self,
        cliente: ClienteUSASpending,
        repositorio: RepositorioEvidencia,
        reloj: Callable[[], datetime] | None = None,
    ):
        self.cliente = cliente
        self.repositorio = repositorio
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))

    def colectar(self, *, limit: int) -> ResultadoUSASpending:
        try:
            awards = self.cliente.buscar_awards(limit=limit)
        except Exception as exc:
            return ResultadoUSASpending(
                requested=limit,
                failed=1,
                failures=[
                    acquisition_failure_from_exception(
                        source="usaspending",
                        operation="search_awards",
                        exc=exc,
                    )
                ],
            )

        accepted = 0
        duplicate = 0
        rejected_records: list[RegistroUSASpendingRechazado] = []
        failures: list[AcquisitionFailure] = []
        for index, award in enumerate(awards, start=1):
            try:
                documento = self._crear_documento(award)
            except ValueError as exc:
                rejected_records.append(
                    RegistroUSASpendingRechazado(index=index, reason=str(exc))
                )
                continue
            try:
                inserted = self.repositorio.guardar_documento_raw(documento)
            except Exception as exc:
                failures.append(
                    acquisition_failure_from_exception(
                        source="usaspending",
                        operation="persist_raw_document",
                        exc=exc,
                        resource_id=documento.source_record_id,
                        category_override=AcquisitionFailureCategory.PERSISTENCE,
                        retryable_override=False,
                    )
                )
                continue

            if inserted:
                accepted += 1
            else:
                duplicate += 1

        if accepted or duplicate:
            self._registrar_fuente_activa()

        return ResultadoUSASpending(
            requested=limit,
            downloaded=len(awards),
            accepted=accepted,
            duplicate=duplicate,
            rejected=len(rejected_records),
            failed=len(failures),
            rejected_records=rejected_records,
            failures=failures,
        )

    def _crear_documento(self, award: dict[str, Any]) -> DocumentoRaw:
        source_record_id = str(
            award.get("generated_internal_id") or award.get("internal_id") or ""
        ).strip()
        if not source_record_id:
            raise ValueError("missing generated_internal_id")

        raw_content = json.dumps(award, ensure_ascii=False, sort_keys=True)
        content_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        return DocumentoRaw(
            source="usaspending",
            source_record_id=source_record_id,
            source_url=f"https://www.usaspending.gov/award/{source_record_id}",
            retrieved_at=self.reloj(),
            content_type="application/json",
            raw_content=raw_content,
            content_hash=content_hash,
            metadata={
                "document_kind": "USASPENDING_AWARD_SEARCH_RESULT",
                "query": USASPENDING_QUERY,
                "recipient_raw": award.get("Recipient Name", "UNKNOWN"),
                "buyer_raw": {
                    "awarding_agency": award.get("Awarding Agency", "UNKNOWN"),
                    "awarding_sub_agency": award.get("Awarding Sub Agency", "UNKNOWN"),
                    "awarding_office": award.get("Awarding Office", "UNKNOWN"),
                },
                "description_raw": award.get("Description")
                or award.get("Contract Description")
                or "UNKNOWN",
                "award_amount_raw": award.get("Award Amount", "UNKNOWN"),
                "potential_award_amount_raw": award.get(
                    "Potential Award Amount", "UNKNOWN"
                ),
                "value_semantics": "award_total",
                "currency_raw": "USD",
                "classification_raw": {
                    "NAICS": award.get("NAICS", "UNKNOWN"),
                    "PSC": award.get("PSC", "UNKNOWN"),
                },
                "date_raw": {
                    "start_date": award.get("Start Date", "UNKNOWN"),
                    "end_date": award.get("End Date", "UNKNOWN"),
                },
                "location_raw": {
                    "state": award.get("Place of Performance State Code", "UNKNOWN"),
                    "country": award.get("Place of Performance Country Code", "UNKNOWN"),
                },
            },
        )

    def _registrar_fuente_activa(self) -> None:
        self.repositorio.guardar_fuente(
            FuenteCandidata(
                name="USASpending.gov Awards API",
                url="https://api.usaspending.gov/api/v2/search/spending_by_award/",
                source_type="public_procurement_api",
                country="US",
                language="en",
                acquisition_method="official_api",
                status="ACTIVE",
                last_checked_at=self.reloj(),
                notes="Technology contracts via NAICS 541511, 541512, 541513, 541519",
                metadata={"query": USASPENDING_QUERY},
            )
        )
