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


class ClienteBusquedaDocumentos(Protocol):
    def buscar(self, *, query: str, limit: int) -> list[dict[str, Any]]:
        """Devuelve registros raw de la fuente externa."""


@dataclass(frozen=True)
class RegistroRechazadoColeccion:
    index: int
    reason: str


@dataclass(frozen=True)
class ResultadoColeccion:
    requested: int
    downloaded: int = 0
    accepted: int = 0
    duplicate: int = 0
    rejected: int = 0
    failed: int = 0
    elapsed_seconds: float = 0.0
    rejected_records: list[RegistroRechazadoColeccion] = field(default_factory=list)
    failures: list[AcquisitionFailure] = field(default_factory=list)


class ColectorDocumentosRaw:
    def __init__(
        self,
        cliente: ClienteBusquedaDocumentos,
        repositorio: RepositorioEvidencia,
        fuente: str,
        reloj: Callable[[], datetime] | None = None,
    ):
        self.cliente = cliente
        self.repositorio = repositorio
        self.fuente = fuente
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))

    def colectar(self, *, query: str, limit: int) -> ResultadoColeccion:
        inicio = datetime.now(timezone.utc)
        try:
            registros = self.cliente.buscar(query=query, limit=limit)
        except Exception as exc:
            return ResultadoColeccion(
                requested=limit,
                failed=1,
                failures=[
                    acquisition_failure_from_exception(
                        source=self.fuente,
                        operation="search",
                        exc=exc,
                    )
                ],
            )

        accepted = 0
        duplicate = 0
        rejected_records: list[RegistroRechazadoColeccion] = []
        failures: list[AcquisitionFailure] = []
        for index, registro in enumerate(registros, start=1):
            try:
                documento = self._crear_documento(registro, query=query)
            except ValueError as exc:
                rejected_records.append(
                    RegistroRechazadoColeccion(index=index, reason=str(exc))
                )
                continue

            try:
                inserted = self.repositorio.guardar_documento_raw(documento)
            except Exception as exc:
                failures.append(
                    acquisition_failure_from_exception(
                        source=self.fuente,
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
            self._registrar_fuente_activa(query=query)

        elapsed = (datetime.now(timezone.utc) - inicio).total_seconds()
        return ResultadoColeccion(
            requested=limit,
            downloaded=len(registros),
            accepted=accepted,
            duplicate=duplicate,
            rejected=len(rejected_records),
            failed=len(failures),
            elapsed_seconds=elapsed,
            rejected_records=rejected_records,
            failures=failures,
        )

    def _crear_documento(self, registro: dict[str, Any], *, query: str) -> DocumentoRaw:
        source_record_id = str(
            registro.get("publication-number") or registro.get("id") or ""
        ).strip()
        if not source_record_id:
            raise ValueError("missing source_record_id")

        raw_content = json.dumps(registro, ensure_ascii=False, sort_keys=True)
        content_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        return DocumentoRaw(
            source=self.fuente,
            source_record_id=source_record_id,
            source_url=self._source_url(registro),
            retrieved_at=self.reloj(),
            content_type="application/json",
            raw_content=raw_content,
            content_hash=content_hash,
            metadata={
                "query": query,
                "publication_date_raw": registro.get("publication-date", "UNKNOWN"),
                "classification_raw": registro.get("classification-cpv", "UNKNOWN"),
                "title_raw": registro.get("notice-title", "UNKNOWN"),
                "buyer_raw": registro.get("buyer-name", "UNKNOWN"),
                "buyer_country_raw": registro.get("buyer-country", "UNKNOWN"),
            },
        )

    @staticmethod
    def _source_url(registro: dict[str, Any]) -> str:
        links = registro.get("links")
        if isinstance(links, dict):
            xml = links.get("xml")
            if isinstance(xml, dict) and xml:
                return str(xml.get("MUL") or next(iter(xml.values())) or "UNKNOWN")
            html = links.get("html")
            if isinstance(html, dict) and html:
                return str(html.get("ENG") or next(iter(html.values())) or "UNKNOWN")
        publication_number = registro.get("publication-number")
        if publication_number:
            return f"https://ted.europa.eu/en/notice/{publication_number}/xml"
        return "UNKNOWN"

    def _registrar_fuente_activa(self, *, query: str) -> None:
        self.repositorio.guardar_fuente(
            FuenteCandidata(
                name="TED - European public procurement",
                url="https://api.ted.europa.eu/v3/notices/search",
                source_type="public_procurement_api",
                country="EU",
                language="multi",
                acquisition_method="official_api",
                status="ACTIVE",
                last_checked_at=self.reloj(),
                notes="TED Public API expert search collector",
                metadata={"query": query},
            )
        )
