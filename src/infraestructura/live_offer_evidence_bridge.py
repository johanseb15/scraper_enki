from __future__ import annotations

import hashlib
from typing import Protocol

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.dominio.offer_evidence import (
    EvidenceLineage,
    OfferReachChargedScopeEvidence,
)


class LiveEvidenceRepository(Protocol):
    """Read-only surface required to project live SQLite lineage."""

    def listar_documentos_raw(
        self,
        source: str | None = None,
        limit: int | None = None,
    ) -> list[DocumentoRaw]:
        ...

    def listar_observaciones_precios_comerciales(
        self,
        extractor_version: str | None = None,
        limit: int | None = None,
    ) -> list[RegistroPrecioComercialObservado]:
        ...


def _unresolved_evidence(
    observation: RegistroPrecioComercialObservado,
    *,
    reason: str,
    raw_document: DocumentoRaw | None = None,
) -> OfferReachChargedScopeEvidence:
    if observation.storage_id is None:
        raise ValueError(
            "Live commercial observation requires storage_id."
        )

    observation_id = str(observation.storage_id)

    raw_hash = (
        raw_document.content_hash
        if raw_document is not None
        else None
    )

    raw_id = (
        f"sha256:{raw_hash}"
        if raw_hash
        else None
    )

    return OfferReachChargedScopeEvidence(
        observation_id=observation_id,
        lineage=EvidenceLineage(
            observation_id=observation_id,
            source_id=observation.source,
            raw_document_id=raw_id,
            source_url=(
                raw_document.source_url
                if raw_document is not None
                else observation.source_url
            ),
            acquired_at=(
                raw_document.retrieved_at.isoformat()
                if raw_document is not None
                else None
            ),
            extractor_version=observation.extractor_version,
            provenance=(
                f"sqlite:raw_documents/"
                f"{observation.raw_document_id}"
            ),
            raw_document_path=None,
            raw_document_hash=raw_hash,
            linkage_status="UNRESOLVED",
            no_linkage_reason=reason,
        ),
    )


def build_live_offer_evidence(
    *,
    repository: LiveEvidenceRepository,
) -> dict[str, OfferReachChargedScopeEvidence]:
    """Project commercial observations to exact SQLite-backed RAW lineage."""

    raw_documents = repository.listar_documentos_raw()

    raw_by_storage_id = {
        document.storage_id: document
        for document in raw_documents
        if document.storage_id is not None
    }

    result: dict[
        str,
        OfferReachChargedScopeEvidence,
    ] = {}

    observations = (
        repository.listar_observaciones_precios_comerciales()
    )

    for observation in observations:
        if observation.storage_id is None:
            raise ValueError(
                "Live commercial observation requires storage_id."
            )

        observation_id = str(
            observation.storage_id
        )

        raw_document = raw_by_storage_id.get(
            observation.raw_document_id
        )

        if raw_document is None:
            result[observation_id] = _unresolved_evidence(
                observation,
                reason="RAW_DOCUMENT_MISSING",
            )
            continue

        if raw_document.source != observation.source:
            result[observation_id] = _unresolved_evidence(
                observation,
                reason="SOURCE_ID_MISMATCH",
                raw_document=raw_document,
            )
            continue

        digest = hashlib.sha256(
            raw_document.raw_content.encode("utf-8")
        ).hexdigest()

        if digest != raw_document.content_hash:
            result[observation_id] = _unresolved_evidence(
                observation,
                reason="RAW_HASH_MISMATCH",
                raw_document=raw_document,
            )
            continue

        result[observation_id] = (
            OfferReachChargedScopeEvidence(
                observation_id=observation_id,
                lineage=EvidenceLineage(
                    observation_id=observation_id,
                    source_id=observation.source,
                    raw_document_id=f"sha256:{digest}",
                    source_url=raw_document.source_url,
                    acquired_at=(
                        raw_document.retrieved_at.isoformat()
                    ),
                    extractor_version=(
                        observation.extractor_version
                    ),
                    provenance=(
                        f"sqlite:raw_documents/"
                        f"{raw_document.storage_id}"
                    ),
                    raw_document_path=None,
                    raw_document_hash=digest,
                    linkage_status="TRACEABLE_RAW",
                ),
            )
        )

    return result
