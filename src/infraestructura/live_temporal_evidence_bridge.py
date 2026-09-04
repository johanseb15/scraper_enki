from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Protocol

from bs4 import BeautifulSoup, NavigableString, Tag

from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroPrecioComercialObservado,
)
from src.dominio.temporal_evidence import (
    TemporalEvidence,
    TemporalEvidenceState,
)
from src.infraestructura.scrapers.generic_price_extractor import (
    extraer_observaciones_precio_genericas,
)


class LiveTemporalEvidenceRepository(Protocol):
    """Read-only surface required for SQLite-backed temporal projection."""

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


_PRICE_CONTEXT_CONTAINER_NAMES = {
    "article",
    "div",
    "li",
    "main",
    "section",
    "table",
    "tr",
}

_MONTH_PATTERN = re.compile(
    r"\b("
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
    r"septiembre|octubre|noviembre|diciembre"
    r")\s+(?:de\s+)?(20\d{2})\b",
    re.IGNORECASE,
)

_PRICE_TIME_MARKERS = (
    "lista de precio",
    "lista de precios",
    "precio orientativo",
    "precios orientativos",
    "tabla de honorario",
    "tabla de honorarios",
)

# Conservative fallback used only to decide whether a sibling DOM branch is
# price-bearing and therefore must be excluded from another offer's context.
_PRICE_TOKEN_PATTERN = re.compile(
    r"(?:\$|ARS)\s*\d|\d[\d.,\s]*\s*ARS\b",
    re.IGNORECASE,
)


def _fold(value: object) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        str(value or ""),
    )
    return " ".join(
        "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )
        .casefold()
        .split()
    )


def _same_offer(
    observation: RegistroPrecioComercialObservado,
    candidate: RegistroPrecioComercialObservado,
) -> bool:
    try:
        same_price = (
            int(candidate.price_value)
            == int(observation.price_value)
        )
    except (TypeError, ValueError):
        return False

    return (
        _fold(candidate.economic_object_raw)
        == _fold(observation.economic_object_raw)
        and same_price
        and str(candidate.currency_raw).strip()
        == str(observation.currency_raw).strip()
    )


def _month_year_candidates(
    raw_basis: str,
) -> tuple[str, ...]:
    values = {
        f"{match.group(1).casefold()} {match.group(2)}"
        for match in _MONTH_PATTERN.finditer(raw_basis)
    }
    return tuple(sorted(values))


def _has_price_time_marker(raw_basis: str) -> bool:
    folded = _fold(raw_basis)
    return any(
        marker in folded
        for marker in _PRICE_TIME_MARKERS
    )


def _observations_in_container(
    container: Tag,
    *,
    observation: RegistroPrecioComercialObservado,
    raw_document: DocumentoRaw,
) -> list[RegistroPrecioComercialObservado]:
    return extraer_observaciones_precio_genericas(
        str(container),
        source=observation.source,
        provider=str(
            observation.provider_raw
            or ""
        ),
        source_url=observation.source_url,
        raw_document_id=(
            raw_document.storage_id
            or 0
        ),
        retrieved_at=raw_document.retrieved_at,
        content_hash=raw_document.content_hash,
    )


def _contains_tag(
    root: Tag,
    target: Tag,
) -> bool:
    if root is target:
        return True

    return any(
        descendant is target
        for descendant in root.descendants
        if isinstance(descendant, Tag)
    )


def _branch_is_price_bearing(
    branch: Tag,
    *,
    observation: RegistroPrecioComercialObservado,
    raw_document: DocumentoRaw,
) -> bool:
    """Return True when a sibling branch contains commercial price content.

    A sibling price branch is a separate applicability branch. Its headings and
    dates must not become temporal evidence for the current offer.
    """

    observed = _observations_in_container(
        branch,
        observation=observation,
        raw_document=raw_document,
    )

    if observed:
        return True

    return bool(
        _PRICE_TOKEN_PATTERN.search(
            branch.get_text(
                " ",
                strip=True,
            )
        )
    )


def _scoped_context_text(
    container: Tag,
    *,
    anchor: Tag,
    observation: RegistroPrecioComercialObservado,
    raw_document: DocumentoRaw,
) -> str:
    """Build ancestor context without importing sibling price-list branches.

    Direct textual/header siblings remain visible because they can define one
    shared price-list heading for multiple offer children. Sibling subtrees that
    themselves contain prices are excluded, preventing temporal fan-out between
    independent lists nested under a broader section.
    """

    parts: list[str] = []

    for child in container.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                parts.append(text)
            continue

        if not isinstance(child, Tag):
            continue

        if _contains_tag(
            child,
            anchor,
        ):
            text = child.get_text(
                " ",
                strip=True,
            )
            if text:
                parts.append(text)
            continue

        if _branch_is_price_bearing(
            child,
            observation=observation,
            raw_document=raw_document,
        ):
            continue

        text = child.get_text(
            " ",
            strip=True,
        )
        if text:
            parts.append(text)

    return " ".join(
        " ".join(parts).split()
    )


def _tag_depth(tag: Tag) -> int:
    depth = 0
    parent = tag.parent

    while isinstance(parent, Tag):
        depth += 1
        parent = parent.parent

    return depth


def _candidate_text_can_reproduce_offer(
    candidate_text: str,
    *,
    observation: RegistroPrecioComercialObservado,
) -> bool:
    """Cheap fail-closed prefilter before exact generic re-extraction.

    Persisted economic_object_raw may omit the primary price even when that
    exact price is physically interleaved inside the DOM row. Permit only that
    one known transformation: remove one exact folded price_raw occurrence and
    test the persisted object again.

    Final acceptance still requires exact _same_offer() after re-extraction.
    """

    target = _fold(
        observation.economic_object_raw
    )
    if not target:
        return False

    if target in candidate_text:
        return True

    primary_price = _fold(
        observation.price_raw
    )
    if not primary_price:
        return False

    if primary_price not in candidate_text:
        return False

    without_primary_price = " ".join(
        candidate_text.replace(
            primary_price,
            "",
            1,
        ).split()
    )

    return target in without_primary_price


def _find_offer_anchor(
    observation: RegistroPrecioComercialObservado,
    *,
    raw_document: DocumentoRaw,
    soup: BeautifulSoup,
) -> Tag | None:
    """Find the most specific DOM node reproducing the persisted offer."""

    target = _fold(
        observation.economic_object_raw
    )
    if not target:
        return None

    best_candidate: Tag | None = None
    best_depth = -1

    for candidate in soup.find_all(True):
        if not isinstance(candidate, Tag):
            continue

        if candidate.name in {
            "body",
            "html",
        }:
            continue

        candidate_text = _fold(
            candidate.get_text(
                " ",
                strip=True,
            )
        )

        if not _candidate_text_can_reproduce_offer(
            candidate_text,
            observation=observation,
        ):
            continue

        observed = _observations_in_container(
            candidate,
            observation=observation,
            raw_document=raw_document,
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
            continue

        candidate_depth = _tag_depth(
            candidate
        )

        if candidate_depth > best_depth:
            best_candidate = candidate
            best_depth = candidate_depth

    return best_candidate


def _price_time_from_offer_context(
    observation: RegistroPrecioComercialObservado,
    *,
    raw_document: DocumentoRaw,
) -> tuple[
    str | None,
    tuple[str, ...],
    tuple[str, ...],
]:
    """Resolve bounded price-time context only after inspecting all ancestors.

    There is deliberately no whole-document/body fallback. Page publication
    dates, footer dates and temporal text inside sibling price branches are not
    admissible as temporal evidence for the current observation.

    If multiple distinct month/year values apply along the exact offer ancestry,
    the bridge preserves a temporal conflict instead of choosing the nearest
    container or any arbitrary value.
    """

    if "html" not in str(
        raw_document.content_type
        or ""
    ).casefold():
        return None, (), ()

    if raw_document.storage_id is None:
        return None, (), ()

    soup = BeautifulSoup(
        raw_document.raw_content,
        "html.parser",
    )

    anchor = _find_offer_anchor(
        observation,
        raw_document=raw_document,
        soup=soup,
    )

    if anchor is None:
        return None, (), ()

    container: Tag | None = anchor
    seen_containers: set[int] = set()
    applicable_values: set[str] = set()
    provenance: set[str] = set()

    while isinstance(container, Tag):
        if container.name in {
            "body",
            "html",
        }:
            break

        if (
            container.name
            in _PRICE_CONTEXT_CONTAINER_NAMES
        ):
            identity = id(container)

            if identity not in seen_containers:
                seen_containers.add(identity)

                raw_basis = _scoped_context_text(
                    container,
                    anchor=anchor,
                    observation=observation,
                    raw_document=raw_document,
                )

                month_years = (
                    _month_year_candidates(
                        raw_basis
                    )
                )

                if (
                    month_years
                    and _has_price_time_marker(
                        raw_basis
                    )
                ):
                    applicable_values.update(
                        month_years
                    )
                    provenance.add(
                        "sqlite:raw_documents/"
                        f"{raw_document.storage_id}"
                        f"#{container.name}"
                        "-price-time-context"
                    )

        parent = container.parent
        container = (
            parent
            if isinstance(parent, Tag)
            else None
        )

    if len(applicable_values) > 1:
        return (
            None,
            tuple(sorted(provenance)),
            (
                "MULTIPLE_APPLICABLE_PRICE_TIME_CONTEXTS",
            ),
        )

    if len(applicable_values) == 1:
        return (
            next(iter(applicable_values)),
            tuple(sorted(provenance)),
            (),
        )

    return None, tuple(sorted(provenance)), ()


def _unknown_evidence(
    observation: RegistroPrecioComercialObservado,
    *,
    reason: str,
) -> TemporalEvidence:
    if observation.storage_id is None:
        raise ValueError(
            "Live commercial observation requires storage_id."
        )

    return TemporalEvidence(
        observation_id=str(
            observation.storage_id
        ),
        source_id=observation.source,
        extractor_version=(
            observation.extractor_version
        ),
        temporal_state=(
            TemporalEvidenceState.TEMPORAL_UNKNOWN
        ),
        temporal_identity_known=False,
        freshness_policy_known=False,
        provenance=(
            "sqlite:raw_documents/"
            f"{observation.raw_document_id}"
            f"#{reason}",
        ),
        filesystem_dates_used_as_evidence=False,
    )


def _mismatch_evidence(
    observation: RegistroPrecioComercialObservado,
    *,
    raw_document: DocumentoRaw,
    reason: str,
    digest: str | None = None,
) -> TemporalEvidence:
    if observation.storage_id is None:
        raise ValueError(
            "Live commercial observation requires storage_id."
        )

    return TemporalEvidence(
        observation_id=str(
            observation.storage_id
        ),
        source_id=observation.source,
        extractor_version=(
            observation.extractor_version
        ),
        raw_document_id=(
            f"sha256:{digest}"
            if digest
            else None
        ),
        acquired_at=(
            raw_document.retrieved_at.isoformat()
        ),
        temporal_state=(
            TemporalEvidenceState.TEMPORAL_MISMATCH
        ),
        temporal_identity_known=False,
        freshness_policy_known=False,
        provenance=(
            "sqlite:raw_documents/"
            f"{raw_document.storage_id}"
            f"#{reason}",
        ),
        conflicts=(reason,),
        filesystem_dates_used_as_evidence=False,
    )


def build_live_temporal_evidence(
    *,
    repository: LiveTemporalEvidenceRepository,
) -> dict[str, TemporalEvidence]:
    """Project live SQLite observations to fail-closed temporal evidence."""

    raw_documents = (
        repository.listar_documentos_raw()
    )

    raw_by_storage_id = {
        document.storage_id: document
        for document in raw_documents
        if document.storage_id is not None
    }

    result: dict[str, TemporalEvidence] = {}

    observations = (
        repository
        .listar_observaciones_precios_comerciales()
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
            result[observation_id] = (
                _unknown_evidence(
                    observation,
                    reason="RAW_DOCUMENT_MISSING",
                )
            )
            continue

        digest = hashlib.sha256(
            raw_document.raw_content.encode(
                "utf-8"
            )
        ).hexdigest()

        if (
            digest
            != raw_document.content_hash
        ):
            result[observation_id] = (
                _mismatch_evidence(
                    observation,
                    raw_document=raw_document,
                    reason="RAW_HASH_MISMATCH",
                    digest=digest,
                )
            )
            continue

        if (
            raw_document.source
            != observation.source
        ):
            result[observation_id] = (
                _mismatch_evidence(
                    observation,
                    raw_document=raw_document,
                    reason="SOURCE_ID_MISMATCH",
                    digest=digest,
                )
            )
            continue

        (
            price_time,
            price_time_provenance,
            price_time_conflicts,
        ) = _price_time_from_offer_context(
            observation,
            raw_document=raw_document,
        )

        provenance = [
            "sqlite:raw_documents/"
            f"{raw_document.storage_id}"
        ]
        provenance.extend(
            price_time_provenance
        )

        result[observation_id] = (
            TemporalEvidence(
                observation_id=observation_id,
                source_id=observation.source,
                extractor_version=(
                    observation.extractor_version
                ),
                raw_document_id=(
                    f"sha256:{digest}"
                ),
                acquired_at=(
                    raw_document
                    .retrieved_at
                    .isoformat()
                ),
                price_validity_time_raw=(
                    price_time
                ),
                temporal_state=(
                    TemporalEvidenceState
                    .TEMPORAL_CONFLICT
                    if price_time_conflicts
                    else TemporalEvidenceState
                    .HISTORICAL_REPRODUCIBLE
                ),
                temporal_identity_known=True,
                freshness_policy_known=False,
                freshness_policy_version=None,
                provenance=tuple(provenance),
                conflicts=price_time_conflicts,
                filesystem_dates_used_as_evidence=False,
            )
        )

    return result
