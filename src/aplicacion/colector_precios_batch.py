from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Callable, Protocol

from src.aplicacion.puertos.repositorio_evidencia import (
    RepositorioEvidencia,
)
from src.dominio.evidencia import (
    DocumentoRaw,
    FuenteCandidata,
    RegistroPrecioComercialObservado,
)


class DownloaderHTML(Protocol):
    def descargar(self, url: str) -> str:
        ...


class ExtractorPrecio(Protocol):
    def __call__(
        self,
        html: str,
        *,
        source: str,
        provider: str,
        source_url: str,
        raw_document_id: int,
        retrieved_at: datetime,
        content_hash: str | None = None,
    ) -> list[RegistroPrecioComercialObservado]:
        ...


@dataclass(frozen=True)
class FuentePricing:
    source: str
    provider: str
    url: str
    province: str
    city: str
    extractor_version: str = "generic_price_extractor_v3"


@dataclass(frozen=True)
class FalloFuentePricing:
    source: str
    provider: str
    url: str
    error: str


@dataclass(frozen=True)
class ResultadoBatchPricing:
    sources_attempted: int = 0
    sources_succeeded: int = 0
    sources_failed: int = 0

    raw_docs_acquired: int = 0
    raw_docs_duplicate: int = 0

    observations_extracted: int = 0
    observations_duplicate: int = 0
    exact_prices: int = 0

    failures: tuple[FalloFuentePricing, ...] = ()


def _buscar_documento_raw(
    repositorio: RepositorioEvidencia,
    *,
    source: str,
    source_url: str,
    content_hash: str,
):
    documentos = repositorio.listar_documentos_raw(
        source=source
    )

    return next(
        documento
        for documento in documentos
        if documento.source_record_id == source_url
        and documento.content_hash == content_hash
    )


def colectar_fuentes_pricing(
    fuentes: list[FuentePricing],
    *,
    repositorio: RepositorioEvidencia,
    downloader: DownloaderHTML,
    extractor: ExtractorPrecio,
    reloj: Callable[[], datetime] | None = None,
) -> ResultadoBatchPricing:
    now = reloj or (
        lambda: datetime.now(timezone.utc)
    )

    sources_succeeded = 0
    sources_failed = 0

    raw_docs_acquired = 0
    raw_docs_duplicate = 0

    observations_extracted = 0
    observations_duplicate = 0
    exact_prices = 0

    failures: list[FalloFuentePricing] = []

    for fuente in fuentes:
        try:
            retrieved_at = now()

            html = downloader.descargar(
                fuente.url
            )

            content_hash = hashlib.sha256(
                html.encode("utf-8")
            ).hexdigest()

            documento = DocumentoRaw(
                source=fuente.source,
                source_record_id=fuente.url,
                source_url=fuente.url,
                retrieved_at=retrieved_at,
                content_type="text/html",
                raw_content=html,
                content_hash=content_hash,
                metadata={
                    "provider_name": fuente.provider,
                    "province": fuente.province,
                    "city": fuente.city,
                    "extractor_version": (
                        fuente.extractor_version
                    ),
                },
            )

            raw_inserted = (
                repositorio
                .guardar_documento_raw(
                    documento
                )
            )

            if raw_inserted:
                raw_docs_acquired += 1
            else:
                raw_docs_duplicate += 1

            raw_document = (
                _buscar_documento_raw(
                    repositorio,
                    source=fuente.source,
                    source_url=fuente.url,
                    content_hash=content_hash,
                )
            )

            observaciones = extractor(
                raw_document.raw_content,
                source=fuente.source,
                provider=fuente.provider,
                source_url=raw_document.source_url,
                raw_document_id=(
                    raw_document.storage_id or 0
                ),
                retrieved_at=(
                    raw_document.retrieved_at
                ),
                content_hash=(
                    raw_document.content_hash
                ),
            )

            for observacion in observaciones:
                inserted = (
                    repositorio
                    .guardar_observacion_precio_comercial(
                        observacion
                    )
                )

                if inserted:
                    observations_extracted += 1
                else:
                    observations_duplicate += 1

            exact_prices += sum(
                1
                for observacion in observaciones
                if observacion.price_value
                is not None
            )

            repositorio.guardar_fuente(
                FuenteCandidata(
                    name=fuente.provider,
                    url=fuente.url,
                    source_type=(
                        "commercial_price_page"
                    ),
                    country="AR",
                    language="es",
                    acquisition_method="http_html",
                    status="ACTIVE",
                    last_checked_at=retrieved_at,
                    notes=(
                        "Generic automatic "
                        "pricing acquisition"
                    ),
                    metadata={
                        "source": fuente.source,
                        "province": fuente.province,
                        "city": fuente.city,
                        "extractor_version": (
                            fuente.extractor_version
                        ),
                    },
                )
            )

            sources_succeeded += 1

        except Exception as exc:
            sources_failed += 1

            failures.append(
                FalloFuentePricing(
                    source=fuente.source,
                    provider=fuente.provider,
                    url=fuente.url,
                    error=str(exc),
                )
            )

    return ResultadoBatchPricing(
        sources_attempted=len(fuentes),
        sources_succeeded=sources_succeeded,
        sources_failed=sources_failed,
        raw_docs_acquired=raw_docs_acquired,
        raw_docs_duplicate=raw_docs_duplicate,
        observations_extracted=(
            observations_extracted
        ),
        observations_duplicate=(
            observations_duplicate
        ),
        exact_prices=exact_prices,
        failures=tuple(failures),
    )
