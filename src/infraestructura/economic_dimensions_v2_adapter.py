from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re
import unicodedata

from src.aplicacion.pricing_dimensions import infer_price_scope
from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    EconomicEvidenceDimensionsV2,
    LocationDimension,
    ProviderIdentity,
    resolve_scalar_dimension,
    resolve_set_dimension,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.offer_evidence import SourceEconomicClaim


DIMENSIONS_V2_VERSION = "economic-evidence-dimensions-v2"


def derive_economic_dimensions_v2(
    row: Mapping[str, object],
    source_registry: Mapping[str, Mapping[str, object]],
    source_claims: tuple[SourceEconomicClaim, ...] = (),
) -> EconomicEvidenceDimensionsV2:
    observation_id = _clean(row.get("observation_id")) or "UNKNOWN"
    source = _clean(row.get("source"))
    raw = _clean(row.get("economic_object_raw"))
    folded = _fold(raw)

    reference = f"source={source or 'UNKNOWN'};observation_id={observation_id}"
    raw_provenance = KnowledgeProvenance(
        "RAW_SOURCE_EXPRESSION",
        f"{reference};field=economic_object_raw",
        _clean(row.get("extractor_version")) or None,
    )
    normalized_provenance = KnowledgeProvenance(
        "SEMANTIC_NORMALIZATION_FIELD",
        f"{reference};artifact=semantic_normalization_v4",
        "semantic-normalization-v4",
    )
    derived_provenance = KnowledgeProvenance(
        "ECONOMIC_DIMENSION_DERIVATION",
        f"{reference};schema=v2",
        DIMENSIONS_V2_VERSION,
    )

    provider_claims = []
    registry_row = source_registry.get(source)
    if registry_row:
        provider_name = _clean(registry_row.get("provider"))
        if provider_name:
            provider_claims.append(DimensionClaim(
                _provider_identity(provider_name, source),
                DimensionOrigin.REGISTRY_CLAIM,
                KnowledgeProvenance(
                    "PROVIDER_SOURCE_REGISTRY",
                    f"source={source};provider={provider_name}",
                    "pricing-source-registry-v1",
                ),
                f"registry source={source!r} provider={provider_name!r}",
            ))
    normalized_provider = _clean(row.get("provider")) or _clean(row.get("provider_name"))
    if normalized_provider:
        provider_claims.append(DimensionClaim(
            _provider_identity(normalized_provider, source),
            DimensionOrigin.NORMALIZED_FIELD,
            normalized_provenance,
            f"normalized provider={normalized_provider!r}",
        ))

    price_scope_claims = []
    price_scope_claims.extend(
        _dimension_claim_from_source(claim, _charged_unit_to_scope(claim.value))
        for claim in source_claims
        if claim.dimension == "charged_unit" and _charged_unit_to_scope(claim.value)
    )
    explicit_scope = _explicit_price_scope(folded)
    if explicit_scope:
        price_scope_claims.append(DimensionClaim(
            explicit_scope,
            DimensionOrigin.RAW_SOURCE_OBSERVATION,
            raw_provenance,
            raw,
        ))
    normalized_scope = _known(_clean(row.get("price_scope")))
    if normalized_scope:
        price_scope_claims.append(DimensionClaim(
            normalized_scope,
            DimensionOrigin.NORMALIZED_FIELD,
            normalized_provenance,
            f"normalized price_scope={normalized_scope}",
        ))

    currency_claims = []
    normalized_currency = _known(_clean(row.get("currency")))
    if normalized_currency:
        currency_claims.append(DimensionClaim(
            normalized_currency.upper(),
            DimensionOrigin.NORMALIZED_FIELD,
            normalized_provenance,
            f"normalized currency={normalized_currency}",
        ))
    for currency in _explicit_currencies(folded):
        currency_claims.append(DimensionClaim(
            currency,
            DimensionOrigin.RAW_SOURCE_OBSERVATION,
            raw_provenance,
            raw,
        ))

    delivery_claims = []
    delivery_claims.extend(
        _dimension_claim_from_source(claim, claim.value)
        for claim in source_claims
        if claim.dimension == "delivery_mode"
    )
    for mode in _explicit_delivery_modes(folded):
        delivery_claims.append(DimensionClaim(
            mode,
            DimensionOrigin.RAW_SOURCE_OBSERVATION,
            raw_provenance,
            raw,
        ))

    reach_claims = []
    reach_claims.extend(
        _dimension_claim_from_source(claim, claim.value)
        for claim in source_claims
        if claim.dimension == "geographic_reach"
    )
    for reach in _explicit_geographic_reach(folded):
        reach_claims.append(DimensionClaim(
            reach,
            DimensionOrigin.RAW_SOURCE_OBSERVATION,
            raw_provenance,
            raw,
        ))

    province = _known(_clean(row.get("province")))
    city = _known(_clean(row.get("city")))
    country = _known(_clean(row.get("country")))
    location_claims = []
    if country or province or city:
        location_claims.append(DimensionClaim(
            LocationDimension(country=country, province=province, city=city),
            DimensionOrigin.NORMALIZED_FIELD,
            normalized_provenance,
            "; ".join(part for part in (
                f"normalized country={country}" if country else "",
                f"normalized province={province}" if province else "",
                f"normalized city={city}" if city else "",
            ) if part),
        ))

    context_claims = tuple(
        DimensionClaim(
            value,
            DimensionOrigin.RAW_SOURCE_OBSERVATION,
            raw_provenance,
            raw,
        )
        for value in _explicit_commercial_contexts(folded)
    )

    role = _clean(row.get("semantic_role"))
    bundle_claims = []
    bundle_value = {
        "COMPOSITE_SERVICE": "COMPOSITE",
        "SINGLE_SERVICE": "SIMPLE",
        "HARDWARE_PRODUCT": "HARDWARE_PRODUCT",
    }.get(role)
    if bundle_value:
        bundle_claims.append(DimensionClaim(
            bundle_value,
            DimensionOrigin.DERIVED_CLAIM,
            derived_provenance,
            f"semantic_role={role}",
        ))

    hardware_claims = []
    if role == "HARDWARE_PRODUCT":
        hardware_claims.append(DimensionClaim(
            True, DimensionOrigin.DERIVED_CLAIM, derived_provenance,
            "semantic_role=HARDWARE_PRODUCT",
        ))
    elif re.search(r"\b(?:incluye|con|cambio a)\s+(?:ssd|disco|memoria|repuesto|hardware)\b", folded):
        hardware_claims.append(DimensionClaim(
            True, DimensionOrigin.RAW_SOURCE_OBSERVATION, raw_provenance, raw
        ))
    elif re.search(r"\bsin\s+(?:repuestos?|hardware|disco|ssd|memoria)\b", folded):
        hardware_claims.append(DimensionClaim(
            False, DimensionOrigin.RAW_SOURCE_OBSERVATION, raw_provenance, raw
        ))

    materials_claims = []
    if re.search(r"\b(?:incluye|con)\s+material(?:es)?\b|\bmateriales? incluidos?\b", folded):
        materials_claims.append(DimensionClaim(
            True, DimensionOrigin.RAW_SOURCE_OBSERVATION, raw_provenance, raw
        ))
    elif re.search(r"\bsin\s+material(?:es)?\b|\bmateriales? (?:aparte|no incluidos?)\b", folded):
        materials_claims.append(DimensionClaim(
            False, DimensionOrigin.RAW_SOURCE_OBSERVATION, raw_provenance, raw
        ))

    device_claims = tuple(
        DimensionClaim(
            device,
            DimensionOrigin.RAW_SOURCE_OBSERVATION,
            raw_provenance,
            raw,
        )
        for device in _explicit_device_scopes(folded)
    )

    return EconomicEvidenceDimensionsV2(
        provider_identity=resolve_scalar_dimension(*provider_claims),
        price_scope=resolve_scalar_dimension(*price_scope_claims),
        currency=resolve_scalar_dimension(*currency_claims),
        delivery_mode=resolve_scalar_dimension(*delivery_claims),
        geographic_reach=resolve_scalar_dimension(*reach_claims),
        location=resolve_scalar_dimension(*location_claims),
        commercial_context=resolve_set_dimension(
            *context_claims,
            incompatible_pairs=tuple(
                ("STANDARD", value)
                for value in (
                    "URGENCY", "AFTER_HOURS", "WEEKEND_HOLIDAY",
                    "PROMOTION", "DISCOUNT",
                )
            ),
        ),
        bundle_status=resolve_scalar_dimension(*bundle_claims),
        hardware_included=resolve_scalar_dimension(*hardware_claims),
        materials_included=resolve_scalar_dimension(*materials_claims),
        device_scope=resolve_set_dimension(*device_claims),
    )


def _dimension_claim_from_source(claim: SourceEconomicClaim, value: str) -> DimensionClaim[str]:
    return DimensionClaim(
        value,
        DimensionOrigin.RAW_SOURCE_OBSERVATION,
        KnowledgeProvenance(
            claim.extraction_method.value,
            f"raw_document_id={claim.raw_document_id};provenance={claim.provenance}",
            claim.version,
        ),
        claim.raw_basis,
    )


def _charged_unit_to_scope(value: str) -> str | None:
    return {
        "HOUR": "PER_HOUR",
        "VISIT": "PER_VISIT",
        "UNIT": "PER_UNIT",
        "MONTH": "PER_MONTH",
        "PROJECT": "PER_PROJECT",
        "TOTAL": "TOTAL",
    }.get(value)


def _explicit_delivery_modes(text: str) -> tuple[str, ...]:
    if re.search(r"\bhibrid[oa]\b|\bremot[oa]\s+(?:y|o)\s+presencial\b", text):
        return ("HYBRID",)
    modes = []
    if re.search(r"\bremot[oa]\b|\ba distancia\b|\bacceso remoto\b", text):
        modes.append("REMOTE")
    if re.search(r"\bpresencial\b|\ben local\b|\ba domicilio\b|\bon[ -]?site\b", text):
        modes.append("ONSITE")
    return tuple(modes)


def _explicit_geographic_reach(text: str) -> tuple[str, ...]:
    if re.search(r"\btodo el pais\b|\ben todo el pais\b|\bcobertura nacional\b|\ba nivel nacional\b", text):
        return ("NATIONAL",)
    if re.search(r"\bmultiples provincias\b|\bvarias provincias\b", text):
        return ("MULTI_PROVINCE",)
    return ()


def _explicit_price_scope(text: str) -> str | None:
    existing = infer_price_scope(text)
    if existing != "UNKNOWN":
        return existing
    if re.search(r"\bdesde\b|\ba partir de\b", text):
        return "LOWER_BOUND"
    if re.search(r"\bprecio total\b|\btotal(?: final)?\b", text):
        return "TOTAL"
    return None


def _explicit_commercial_contexts(text: str) -> tuple[str, ...]:
    contexts = []
    for pattern, value in (
        (r"\burgenc(?:ia|ias)\b|\burgente\b|\bemergenc(?:ia|ias)\b", "URGENCY"),
        (r"\bfuera de (?:horario|hs)\b|\bafter hours?\b", "AFTER_HOURS"),
        (r"\bfin(?:es)? de semana\b|\bferiado(?:s)?\b", "WEEKEND_HOLIDAY"),
        (r"\bpromocion\b|\bpromo\b", "PROMOTION"),
        (r"\bdescuento\b|\boff\b", "DISCOUNT"),
        (r"\bprecio (?:regular|estandar)\b|\btarifa estandar\b", "STANDARD"),
    ):
        if re.search(pattern, text):
            contexts.append(value)
    return tuple(contexts)


def _explicit_device_scopes(text: str) -> tuple[str, ...]:
    values = []
    without_pc_gamer = re.sub(r"\bpc gamer\b", " ", text)
    for pattern, value, target in (
        (r"\bpc gamer\b", "PC_GAMER", text),
        (r"\bnotebooks?\b", "NOTEBOOK", text),
        (r"\b(?:pc|computadora)(?:s)?\b", "PC", without_pc_gamer),
        (r"\bservidores?\b", "SERVER", text),
        (r"\bcamaras?\b", "CAMERA", text),
        (r"\bimpresoras?\b", "PRINTER", text),
    ):
        if re.search(pattern, target):
            values.append(value)
    return tuple(values)


def _explicit_currencies(text: str) -> tuple[str, ...]:
    currencies = []
    if re.search(r"\bu\$s\b|\busd\b|\bdolares?\b", text):
        currencies.append("USD")
    if re.search(r"\bars\b|\bpesos?\b", text):
        currencies.append("ARS")
    return tuple(currencies)


def _provider_identity(provider_name: str, source: str) -> ProviderIdentity:
    identity_basis = " ".join(
        unicodedata.normalize("NFKC", provider_name).casefold().split()
    )
    digest = hashlib.sha256(identity_basis.encode("utf-8")).hexdigest()[:12]
    return ProviderIdentity(
        provider_id=f"provider:{_slug(provider_name)}:{digest}",
        provider_name=provider_name,
        source=source,
    )


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .split()
    )


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _fold(value)).strip("-")


def _known(value: str) -> str | None:
    return None if not value or value.upper() in {"UNKNOWN", "NONE", "N/A"} else value


def _clean(value: object) -> str:
    return str(value or "").strip()
