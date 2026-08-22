from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from src.dominio.offer_evidence import (
    ChargedUnit,
    PriceBound,
    SourceClaimMethod,
    SourceEconomicClaim,
)


EXTRACTOR_VERSION = "offer-reach-charged-scope-extractor-v1"


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return " ".join(
        "".join(ch for ch in normalized if not unicodedata.combining(ch))
        .casefold()
        .split()
    )


def extract_claims_from_explicit_basis(
    *,
    observation_id: str,
    raw_basis: str,
    raw_document_id: str,
    provenance: str,
    method: SourceClaimMethod = SourceClaimMethod.DERIVED_FROM_SOURCE_TEXT,
) -> tuple[SourceEconomicClaim, ...]:
    """Extract only claims explicitly stated in an observation-local raw basis."""
    text = _fold(raw_basis)
    claims: list[SourceEconomicClaim] = []

    def add(dimension: str, value: str, qualifiers: Iterable[str] = ()) -> None:
        claims.append(SourceEconomicClaim(
            observation_id=observation_id,
            dimension=dimension,
            value=value,
            raw_basis=raw_basis,
            raw_document_id=raw_document_id,
            extraction_method=method,
            provenance=provenance,
            qualifiers=tuple(qualifiers),
        ))

    if re.search(r"\bremot[oa]\b|\ba distancia\b|\bacceso remoto\b|\bconexion remota\b", text):
        add("delivery_mode", "REMOTE")
    if re.search(r"\bpresencial\b|\ba domicilio\b|\bon[ -]?site\b|\ben taller\b|\bfreelance / taller\b", text):
        add("delivery_mode", "ONSITE")

    # National service reach requires an explicit service/attention/coverage
    # statement. Product shipment language is deliberately excluded.
    if (
        re.search(r"\b(?:servicio|atencion|cobertura|soporte)\b", text)
        and re.search(r"\b(?:todo el pais|nivel nacional|cobertura nacional)\b", text)
        and not re.search(r"\b(?:envio|enviamos|correo|despacho)\b", text)
    ):
        add("geographic_reach", "NATIONAL")
    elif match := re.search(
        r"\bzona de atencion\s*:\s*([a-z ]{3,30})\s+y\s+([a-z ]{3,30})(?:[.;]|$)",
        text,
    ):
        areas = "|".join(" ".join(value.split()).title() for value in match.groups())
        add("geographic_reach", f"NAMED_AREAS:{areas}")
    elif re.search(r"\b(?:atendemos|zona de atencion|cobertura)\b[^.;]{0,50}\bcordoba capital\b", text):
        add("geographic_reach", "CITY:Córdoba Capital")
    elif re.search(r"\b(?:atendemos|zona de atencion|cobertura)\b[^.;]{0,50}\bprovincia de cordoba\b", text):
        add("geographic_reach", "PROVINCE:Córdoba")

    if re.search(r"\bx\s*1\s*(?:hs?|hora)\b|\bpor hora\b|\bla hora\b|\bhora (?:inicial|adicional)\b", text):
        add("charged_unit", ChargedUnit.HOUR.value)
    elif re.search(r"\bpor visita\b|\bcada visita\b|\bvisita tecnica\b", text):
        add("charged_unit", ChargedUnit.VISIT.value)
    elif re.search(r"\bpor (?:equipo|unidad|pc|notebook)\b|\bprecios por equipo\b", text):
        add("charged_unit", ChargedUnit.UNIT.value)
    elif re.search(r"\bpor mes\b|\bal mes\b|\babono mensual\b|\bmensual(?:mente)?\b", text):
        add("charged_unit", ChargedUnit.MONTH.value)
    elif re.search(r"\bpor proyecto\b", text):
        add("charged_unit", ChargedUnit.PROJECT.value)
    elif re.search(r"\bprecio (?:cerrado|total)\b|\btotal final\b", text):
        add("charged_unit", ChargedUnit.TOTAL.value)

    if re.search(r"\bdesde\b|\ba partir de\b", text):
        add("price_bound", PriceBound.LOWER_BOUND.value)
    elif re.search(r"\bprecio minimo\b|\bminimo\b", text):
        add("price_bound", PriceBound.MINIMUM.value)
    elif re.search(r"\bpresupuesto\b|\bconsultar\b", text):
        add("price_bound", PriceBound.QUOTE_REQUIRED.value)
    elif re.search(r"\bprecio (?:cerrado|exacto|total)\b|\btotal final\b", text):
        add("price_bound", PriceBound.EXACT.value)

    qualifiers = []
    for pattern, value in (
        (r"\bviaticos?\b", "TRAVEL_EXPENSES"),
        (r"\btraslado\b", "TRAVEL"),
        (r"\bfuera de zona\b|\badicional por distancia\b|\bkilometros?\b", "DISTANCE_RESTRICTION"),
        (r"\bconsultar (?:disponibilidad|zona)\b|\bsegun ubicacion\b", "AVAILABILITY_RESTRICTION"),
    ):
        if re.search(pattern, text):
            qualifiers.append(value)
    for qualifier in qualifiers:
        add("travel_restriction", qualifier)

    if re.search(r"\b(?:no incluye|sin incluir|sin)\s+(?:repuestos?|hardware|dispositivo|componentes?)\b", text):
        add("hardware_included", "false")
    elif re.search(r"\bincluye\s+(?:repuestos?|hardware|dispositivo|componentes?)\b", text):
        add("hardware_included", "true")
    if re.search(r"\b(?:no incluye|sin incluir|sin)\s+material(?:es)?\b|\bmateriales? (?:aparte|no incluidos?)\b", text):
        add("materials_included", "false")
    elif re.search(r"\bincluye\s+material(?:es)?\b|\bmateriales? incluidos?\b", text):
        add("materials_included", "true")

    return _deduplicate(claims)


def _deduplicate(claims: Iterable[SourceEconomicClaim]) -> tuple[SourceEconomicClaim, ...]:
    result = []
    seen = set()
    for claim in claims:
        identity = (claim.dimension, claim.value, claim.raw_basis, claim.raw_document_id)
        if identity not in seen:
            seen.add(identity)
            result.append(claim)
    return tuple(result)
