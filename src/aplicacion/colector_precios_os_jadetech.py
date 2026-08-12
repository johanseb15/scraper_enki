from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Callable, Protocol

from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import (
    DocumentoRaw,
    FuenteCandidata,
    RegistroPrecioComercialObservado,
)


URL_JADETECH_SERVICIO_TECNICO = "https://jadetech.com.ar/categoria/servicio-tecnico/"
SOURCE = "jadetech_os_installation"
PROVIDER = "Jadetech"
EXTRACTOR_VERSION = "jadetech_os_installation_v1"


class DownloaderHTML(Protocol):
    def descargar(self, url: str) -> str:
        """Descarga HTML desde una URL."""


ParserPrecioComercial = Callable[..., list[RegistroPrecioComercialObservado]]


@dataclass(frozen=True)
class ResultadoColeccionPrecioComercial:
    raw_docs_acquired: int = 0
    raw_docs_duplicate: int = 0
    observations_extracted: int = 0
    observations_duplicate: int = 0
    exact_prices: int = 0
    candidate_comparable_core: int = 0
    indeterminate: int = 0
    rejected: int = 0
    providers: tuple[str, ...] = ()


class ColectorPreciosOSJadetech:
    def __init__(
        self,
        repositorio: RepositorioEvidencia,
        downloader: DownloaderHTML,
        parser_observaciones: ParserPrecioComercial,
        reloj: Callable[[], datetime] | None = None,
        source_url: str = URL_JADETECH_SERVICIO_TECNICO,
        source: str = SOURCE,
        provider: str = PROVIDER,
        extractor_version: str = EXTRACTOR_VERSION,
        source_notes: str = "OS installation/formateo without backup collector source",
    ):
        self.repositorio = repositorio
        self.downloader = downloader
        self.parser_observaciones = parser_observaciones
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))
        self.source_url = source_url
        self.source = source
        self.provider = provider
        self.extractor_version = extractor_version
        self.source_notes = source_notes

    def colectar(self) -> ResultadoColeccionPrecioComercial:
        retrieved_at = self.reloj()
        html = self.downloader.descargar(self.source_url)
        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        documento = DocumentoRaw(
            source=self.source,
            source_record_id=self.source_url,
            source_url=self.source_url,
            retrieved_at=retrieved_at,
            content_type="text/html",
            raw_content=html,
            content_hash=content_hash,
            metadata={
                "provider_name": self.provider,
                "extractor_version": self.extractor_version,
            },
        )
        raw_inserted = self.repositorio.guardar_documento_raw(documento)
        raw_docs = self.repositorio.listar_documentos_raw(source=self.source)
        raw_document = next(
            doc
            for doc in raw_docs
            if doc.source_record_id == self.source_url
            and doc.content_hash == content_hash
        )
        observaciones = self.parser_observaciones(
            raw_document.raw_content,
            source_url=raw_document.source_url,
            raw_document_id=raw_document.storage_id or 0,
            retrieved_at=raw_document.retrieved_at,
            content_hash=raw_document.content_hash,
        )
        inserted = 0
        duplicates = 0
        for observacion in observaciones:
            if self.repositorio.guardar_observacion_precio_comercial(observacion):
                inserted += 1
            else:
                duplicates += 1
        self.repositorio.guardar_fuente(
            FuenteCandidata(
                name=self.provider,
                url=self.source_url,
                source_type="commercial_price_page",
                country="AR",
                language="es",
                acquisition_method="http_html",
                status="ACTIVE",
                last_checked_at=retrieved_at,
                notes=self.source_notes,
                metadata={"extractor_version": self.extractor_version},
            )
        )
        return ResultadoColeccionPrecioComercial(
            raw_docs_acquired=1 if raw_inserted else 0,
            raw_docs_duplicate=0 if raw_inserted else 1,
            observations_extracted=inserted,
            observations_duplicate=duplicates,
            exact_prices=sum(1 for obs in observaciones if obs.price_value is not None),
            candidate_comparable_core=sum(
                1 for obs in observaciones if obs.comparable_status == "COMPARABLE_CORE"
            ),
            indeterminate=sum(
                1 for obs in observaciones if obs.comparable_status == "INDETERMINATE"
            ),
            rejected=0,
            providers=(self.provider,),
        )