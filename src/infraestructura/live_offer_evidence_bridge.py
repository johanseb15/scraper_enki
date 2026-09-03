from __future__ import annotations

import hashlib
import unicodedata
from typing import Protocol

from bs4 import BeautifulSoup, Tag

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.dominio.offer_evidence import (
    EvidenceLineage,
    OfferReachChargedScopeEvidence,
    PageScopeEconomicClaim,
    RawDocumentPageScopeEvidence,
)
from src.infraestructura.offer_evidence_extractor import (
    extract_claims_from_explicit_basis,
)
from src.infraestructura.scrapers.generic_price_extractor import (
    extraer_observaciones_precio_genericas,
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


_CONTEXT_CONTAINER_NAMES = {
    "section",
    "article",
    "tr",
    "li",
}

_PAGE_SCOPE_CONTAINER_NAMES = {
    "section",
    "article",
    "main",
}

_PAGE_SCOPE_LOCATION_CONTAINER_MARKERS = {
    "contact",
    "contacto",
    "location",
    "ubicacion",
    "sede",
    "sedes",
    "sucursal",
    "sucursales",
}


def _normalized_text(value: object) -> str:
    return " ".join(
        str(value or "").casefold().split()
    )


def _same_offer(
    observation: RegistroPrecioComercialObservado,
    candidate: RegistroPrecioComercialObservado,
) -> bool:
    return (
        _normalized_text(
            candidate.economic_object_raw
        )
        == _normalized_text(
            observation.economic_object_raw
        )
        and int(candidate.price_value)
        == int(observation.price_value)
        and str(candidate.currency_raw).strip()
        == str(observation.currency_raw).strip()
    )


def _observations_in_container(
    container: Tag,
    *,
    raw_document: DocumentoRaw,
) -> list[RegistroPrecioComercialObservado]:
    return extraer_observaciones_precio_genericas(
        str(container),
        source=raw_document.source,
        provider="UNKNOWN",
        source_url=raw_document.source_url,
        raw_document_id=raw_document.storage_id,
        retrieved_at=raw_document.retrieved_at,
        content_hash=raw_document.content_hash,
    )


def _fold_page_scope_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(
            ch
            for ch in normalized
            if not unicodedata.combining(ch)
        )
        .casefold()
        .split()
    )


def _is_logistics_page_scope(raw_basis: str) -> bool:
    text = _fold_page_scope_text(raw_basis)
    return any(
        token in text
        for token in (
            "cadeteria",
            "distribucion",
            "entrega",
            "entregas",
            "envio",
            "envios",
            "mensajeria",
            "despacho",
            "despachos",
            "encomienda",
            "encomiendas",
            "flete",
        )
    )


def _is_provider_location_container(container: Tag) -> bool:
    values = [
        str(container.get("id") or ""),
    ]

    classes = container.get("class") or ()
    values.extend(str(value) for value in classes)

    normalized = {
        _fold_page_scope_text(value)
        for value in values
        if str(value).strip()
    }

    return any(
        marker in value
        for value in normalized
        for marker in _PAGE_SCOPE_LOCATION_CONTAINER_MARKERS
    )


def _page_scope_claims(
    *,
    raw_document: DocumentoRaw,
    raw_document_id: str,
) -> tuple[PageScopeEconomicClaim, ...]:
    """Preserve bounded document-level service reach without offer fan-out."""

    if (
        "html"
        not in str(
            raw_document.content_type or ""
        ).casefold()
    ):
        return ()

    if raw_document.storage_id is None:
        return ()

    soup = BeautifulSoup(
        raw_document.raw_content,
        "html.parser",
    )

    result: list[PageScopeEconomicClaim] = []
    seen: set[tuple[str, str]] = set()

    for container in soup.find_all(
        sorted(_PAGE_SCOPE_CONTAINER_NAMES)
    ):
        if not isinstance(container, Tag):
            continue

        if _is_provider_location_container(container):
            continue

        if _observations_in_container(
            container,
            raw_document=raw_document,
        ):
            continue

        raw_basis = container.get_text(
            " ",
            strip=True,
        )

        if not raw_basis:
            continue

        if _is_logistics_page_scope(raw_basis):
            continue

        extracted = extract_claims_from_explicit_basis(
            observation_id=(
                f"raw-document:{raw_document.storage_id}"
            ),
            raw_basis=raw_basis,
            raw_document_id=raw_document_id,
            provenance=(
                "sqlite:raw_documents/"
                f"{raw_document.storage_id}"
                f"#{container.name}-page-scope"
            ),
        )

        for claim in extracted:
            if claim.dimension != "geographic_reach":
                continue

            identity = (
                claim.dimension,
                claim.value,
            )

            if identity in seen:
                continue

            seen.add(identity)

            result.append(
                PageScopeEconomicClaim(
                    dimension=claim.dimension,
                    value=claim.value,
                    raw_basis=claim.raw_basis,
                    raw_document_id=claim.raw_document_id,
                    extraction_method=claim.extraction_method,
                    provenance=claim.provenance,
                    status=claim.status,
                    qualifiers=claim.qualifiers,
                )
            )

    reach_values = {
        claim.value
        for claim in result
        if claim.dimension == "geographic_reach"
    }

    if len(reach_values) > 1:
        return ()

    return tuple(result)


def build_live_page_scope_evidence(
    *,
    repository: LiveEvidenceRepository,
) -> dict[str, RawDocumentPageScopeEvidence]:
    """Project bounded page-level service scope once per exact RAW document."""

    result: dict[
        str,
        RawDocumentPageScopeEvidence,
    ] = {}

    for raw_document in repository.listar_documentos_raw():
        if raw_document.storage_id is None:
            continue

        digest = hashlib.sha256(
            raw_document.raw_content.encode("utf-8")
        ).hexdigest()

        if digest != raw_document.content_hash:
            continue

        raw_document_id = f"sha256:{digest}"

        claims = _page_scope_claims(
            raw_document=raw_document,
            raw_document_id=raw_document_id,
        )

        result[raw_document_id] = (
            RawDocumentPageScopeEvidence(
                raw_document_id=raw_document_id,
                source_id=raw_document.source,
                source_url=raw_document.source_url,
                acquired_at=(
                    raw_document.retrieved_at.isoformat()
                ),
                claims=claims,
            )
        )

    return result


def _offer_applicable_context_claims(
    observation: RegistroPrecioComercialObservado,
    *,
    raw_document: DocumentoRaw,
    raw_document_id: str,
):
    """Extract reach only from a RAW container that reproduces the offer.

    There is deliberately no whole-document fallback: a claim from another
    section, footer or product-shipping block must not become service reach.
    """

    if (
        "html"
        not in str(
            raw_document.content_type or ""
        ).casefold()
    ):
        return ()

    if raw_document.storage_id is None:
        return ()

    target = _normalized_text(
        observation.economic_object_raw
    )

    if not target:
        return ()

    soup = BeautifulSoup(
        raw_document.raw_content,
        "html.parser",
    )

    seen_containers: set[int] = set()

    for candidate in soup.find_all(True):
        if not isinstance(candidate, Tag):
            continue

        candidate_text = _normalized_text(
            candidate.get_text(
                " ",
                strip=True,
            )
        )

        if candidate_text != target:
            continue

        container: Tag | None = candidate

        while isinstance(container, Tag):
            if container.name in {
                "body",
                "html",
            }:
                break

            if (
                container.name
                in _CONTEXT_CONTAINER_NAMES
            ):
                identity = id(container)

                if identity in seen_containers:
                    break

                seen_containers.add(identity)

                observed = (
                    extraer_observaciones_precio_genericas(
                        str(container),
                        source=observation.source,
                        provider=str(
                            observation.provider_raw
                            or ""
                        ),
                        source_url=(
                            observation.source_url
                        ),
                        raw_document_id=(
                            raw_document.storage_id
                        ),
                        retrieved_at=(
                            raw_document.retrieved_at
                        ),
                        content_hash=(
                            raw_document.content_hash
                        ),
                    )
                )

                matches = [
                    item
                    for item in observed
                    if _same_offer(
                        observation,
                        item,
                    )
                ]

                if len(matches) != 1:
                    break

                raw_basis = container.get_text(
                    " ",
                    strip=True,
                )

                claims = (
                    extract_claims_from_explicit_basis(
                        observation_id=str(
                            observation.storage_id
                        ),
                        raw_basis=raw_basis,
                        raw_document_id=(
                            raw_document_id
                        ),
                        provenance=(
                            "sqlite:raw_documents/"
                            f"{raw_document.storage_id}"
                            f"#{container.name}-context"
                        ),
                    )
                )

                return tuple(
                    claim
                    for claim in claims
                    if claim.dimension
                    == "geographic_reach"
                )

            parent = container.parent

            container = (
                parent
                if isinstance(parent, Tag)
                else None
            )

    # Bounded page context is admissible only when that context
    # independently reproduces exactly one commercial offer and that
    # offer is the persisted observation. This is deliberately not a
    # whole-document/body fallback.
    for container in soup.find_all("main"):
        observed = (
            extraer_observaciones_precio_genericas(
                str(container),
                source=observation.source,
                provider=str(
                    observation.provider_raw
                    or ""
                ),
                source_url=(
                    observation.source_url
                ),
                raw_document_id=(
                    raw_document.storage_id
                ),
                retrieved_at=(
                    raw_document.retrieved_at
                ),
                content_hash=(
                    raw_document.content_hash
                ),
            )
        )

        if len(observed) != 1:
            continue

        if not _same_offer(
            observation,
            observed[0],
        ):
            continue

        raw_basis = container.get_text(
            " ",
            strip=True,
        )

        claims = (
            extract_claims_from_explicit_basis(
                observation_id=str(
                    observation.storage_id
                ),
                raw_basis=raw_basis,
                raw_document_id=(
                    raw_document_id
                ),
                provenance=(
                    "sqlite:raw_documents/"
                    f"{raw_document.storage_id}"
                    "#main-unique-offer-context"
                ),
            )
        )

        return tuple(
            claim
            for claim in claims
            if claim.dimension
            == "geographic_reach"
        )

    return ()


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

        raw_id = f"sha256:{digest}"

        claims = _offer_applicable_context_claims(
            observation,
            raw_document=raw_document,
            raw_document_id=raw_id,
        )

        result[observation_id] = (
            OfferReachChargedScopeEvidence(
                observation_id=observation_id,
                lineage=EvidenceLineage(
                    observation_id=observation_id,
                    source_id=observation.source,
                    raw_document_id=raw_id,
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
                claims=claims,
            )
        )

    return result
