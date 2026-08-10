import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import DocumentoRaw


class ClienteTedFullNotice(Protocol):
    def obtener(self, documento: DocumentoRaw) -> tuple[int, str, str, dict[str, str]]:
        """Devuelve status, content_type, body y headers del full notice oficial."""


@dataclass(frozen=True)
class FalloFullNotice:
    source_record_id: str
    reason: str
    status_code: int | None = None


@dataclass(frozen=True)
class ResultadoEnriquecimientoFullNotice:
    requested: int = 0
    downloaded: int = 0
    accepted: int = 0
    duplicate: int = 0
    not_available: int = 0
    rejected: int = 0
    failed: int = 0
    failures: list[FalloFullNotice] = field(default_factory=list)


class ColectorTedFullNotices:
    def __init__(self, cliente: ClienteTedFullNotice, repositorio: RepositorioEvidencia):
        self.cliente = cliente
        self.repositorio = repositorio

    def enriquecer(
        self, documentos_busqueda: list[DocumentoRaw]
    ) -> ResultadoEnriquecimientoFullNotice:
        downloaded = 0
        accepted = 0
        duplicate = 0
        not_available = 0
        rejected = 0
        failed = 0
        failures: list[FalloFullNotice] = []

        for documento in documentos_busqueda:
            try:
                status_code, content_type, body, headers = self.cliente.obtener(documento)
            except Exception as exc:
                failed += 1
                failures.append(
                    FalloFullNotice(
                        source_record_id=documento.source_record_id,
                        reason=str(exc),
                    )
                )
                continue

            if status_code != 200 or not body:
                not_available += 1
                failures.append(
                    FalloFullNotice(
                        source_record_id=documento.source_record_id,
                        reason=self._not_available_reason(status_code, headers, body),
                        status_code=status_code,
                    )
                )
                continue

            downloaded += 1
            if not self._es_formato_full_notice(content_type, body):
                rejected += 1
                failures.append(
                    FalloFullNotice(
                        source_record_id=documento.source_record_id,
                        reason=f"unexpected content_type={content_type}",
                        status_code=status_code,
                    )
                )
                continue

            full_doc = self._crear_documento_full(documento, content_type, body, headers)
            if self.repositorio.guardar_documento_raw(full_doc):
                accepted += 1
            else:
                duplicate += 1

        return ResultadoEnriquecimientoFullNotice(
            requested=len(documentos_busqueda),
            downloaded=downloaded,
            accepted=accepted,
            duplicate=duplicate,
            not_available=not_available,
            rejected=rejected,
            failed=failed,
            failures=failures,
        )

    @staticmethod
    def _crear_documento_full(
        documento: DocumentoRaw,
        content_type: str,
        body: str,
        headers: dict[str, str],
    ) -> DocumentoRaw:
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        return DocumentoRaw(
            source="ted_full_notice",
            source_record_id=documento.source_record_id,
            source_url=documento.source_url,
            retrieved_at=datetime.now(timezone.utc),
            content_type=content_type or "application/xml",
            raw_content=body,
            content_hash=content_hash,
            metadata={
                "document_kind": "TED_FULL_NOTICE",
                "related_search_document_id": documento.storage_id,
                "related_search_content_hash": documento.content_hash,
                "headers_raw": headers,
            },
        )

    @staticmethod
    def _es_formato_full_notice(content_type: str, body: str) -> bool:
        lowered = (content_type or "").lower()
        stripped = body.lstrip()
        return (
            "xml" in lowered
            or "json" in lowered
            or stripped.startswith("<")
            or stripped.startswith("{")
        )

    @staticmethod
    def _not_available_reason(
        status_code: int, headers: dict[str, str], body: str
    ) -> str:
        waf_action = headers.get("x-amzn-waf-action") or headers.get("X-Amzn-Waf-Action")
        if status_code == 202 and waf_action:
            return f"ted_direct_link_not_available: status=202 waf_action={waf_action}"
        if status_code == 202:
            return "ted_direct_link_not_available: status=202 empty body"
        return f"ted_direct_link_not_available: status={status_code} body_length={len(body)}"
