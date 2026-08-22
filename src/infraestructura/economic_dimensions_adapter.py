from __future__ import annotations

from collections.abc import Mapping
import re
import unicodedata

from src.dominio.economic_evidence import (
    DimensionClaim,
    DimensionOrigin,
    EconomicEvidenceDimensions,
    GeographyDimension,
    ProviderIdentity,
    resolve_dimension,
)
from src.dominio.semantic_knowledge import KnowledgeProvenance


DIMENSIONS_VERSION = "economic-evidence-dimensions-v1"


def derive_economic_dimensions(
    row: Mapping[str, object],
    source_registry: Mapping[str, Mapping[str, object]],
) -> EconomicEvidenceDimensions:
    observation_id = _clean(row.get("observation_id")) or "UNKNOWN"
    source = _clean(row.get("source"))
    raw = _clean(row.get("economic_object_raw"))
    folded = _fold(raw)
    observed_provenance = KnowledgeProvenance(
        "COMMERCIAL_OBSERVATION",
        f"source={source or 'UNKNOWN'};observation_id={observation_id}",
        _clean(row.get("extractor_version")) or None,
    )
    inferred_provenance = KnowledgeProvenance(
        "ECONOMIC_DIMENSION_DERIVATION",
        f"observation_id={observation_id}",
        DIMENSIONS_VERSION,
    )

    provider_claims = []
    registry_row = source_registry.get(source)
    if registry_row:
        provider_name = _clean(registry_row.get("provider"))
        if provider_name:
            provider_claims.append(DimensionClaim(
                ProviderIdentity(
                    provider_id=f"provider:{_slug(provider_name)}",
                    provider_name=provider_name,
                    source=source,
                ),
                DimensionOrigin.INFERRED,
                KnowledgeProvenance(
                    "PROVIDER_SOURCE_REGISTRY",
                    f"source={source};provider={provider_name}",
                    DIMENSIONS_VERSION,
                ),
                f"registry source={source!r} provider={provider_name!r}",
            ))

    price_scope_claims = []
    explicit_scope = _explicit_price_scope(folded)
    if explicit_scope:
        price_scope_claims.append(DimensionClaim(
            explicit_scope,
            DimensionOrigin.OBSERVED,
            observed_provenance,
            raw,
        ))
    normalized_scope = _known(_clean(row.get("price_scope")))
    if normalized_scope:
        price_scope_claims.append(DimensionClaim(
            normalized_scope,
            DimensionOrigin.INFERRED,
            inferred_provenance,
            f"normalized price_scope={normalized_scope}",
        ))

    province = _known(_clean(row.get("province")))
    city = _known(_clean(row.get("city")))
    coverage = None
    if re.search(r"\bremot[oa]\b|\ba distancia\b", folded):
        coverage = "REMOTE"
    elif re.search(r"\bpresencial\b|\ben local\b|\ba domicilio\b|\bon[ -]?site\b", folded):
        coverage = "ONSITE"
    geography_claims = []
    if province or city or coverage:
        geography_claims.append(DimensionClaim(
            GeographyDimension(province=province, city=city, coverage=coverage),
            DimensionOrigin.OBSERVED,
            observed_provenance,
            "; ".join(part for part in (
                f"province={province}" if province else "",
                f"city={city}" if city else "",
                f"coverage={coverage}" if coverage else "",
            ) if part),
        ))

    market_claims = []
    raw_market = None
    if coverage == "REMOTE":
        raw_market = "REMOTE"
    elif coverage == "ONSITE":
        raw_market = "LOCAL_SERVICE"
    if raw_market:
        market_claims.append(DimensionClaim(
            raw_market, DimensionOrigin.OBSERVED, observed_provenance, raw
        ))
    normalized_market = _known(_clean(row.get("market_scope")))
    if normalized_market:
        market_claims.append(DimensionClaim(
            normalized_market,
            DimensionOrigin.INFERRED,
            inferred_provenance,
            f"semantic market_scope={normalized_market}",
        ))

    context_claims = []
    commercial_context = _explicit_commercial_context(folded)
    if commercial_context:
        context_claims.append(DimensionClaim(
            commercial_context, DimensionOrigin.OBSERVED, observed_provenance, raw
        ))

    role = _clean(row.get("semantic_role"))
    bundle_claims = []
    if role == "COMPOSITE_SERVICE":
        bundle_claims.append(DimensionClaim(
            "COMPOSITE", DimensionOrigin.INFERRED, inferred_provenance,
            "semantic_role=COMPOSITE_SERVICE",
        ))
    elif role == "SINGLE_SERVICE":
        bundle_claims.append(DimensionClaim(
            "SIMPLE", DimensionOrigin.INFERRED, inferred_provenance,
            "semantic_role=SINGLE_SERVICE",
        ))
    elif role == "HARDWARE_PRODUCT":
        bundle_claims.append(DimensionClaim(
            "HARDWARE_PRODUCT", DimensionOrigin.INFERRED, inferred_provenance,
            "semantic_role=HARDWARE_PRODUCT",
        ))

    hardware_claims = []
    if role == "HARDWARE_PRODUCT":
        hardware_claims.append(DimensionClaim(
            True, DimensionOrigin.INFERRED, inferred_provenance,
            "semantic_role=HARDWARE_PRODUCT",
        ))
    elif re.search(r"\b(?:incluye|con|cambio a)\s+(?:ssd|disco|memoria|repuesto|hardware)\b", folded):
        hardware_claims.append(DimensionClaim(
            True, DimensionOrigin.OBSERVED, observed_provenance, raw
        ))
    elif re.search(r"\bsin\s+(?:repuestos?|hardware|disco|ssd|memoria)\b", folded):
        hardware_claims.append(DimensionClaim(
            False, DimensionOrigin.OBSERVED, observed_provenance, raw
        ))

    materials_claims = []
    if re.search(r"\b(?:incluye|con)\s+material(?:es)?\b|\bmateriales? incluidos?\b", folded):
        materials_claims.append(DimensionClaim(
            True, DimensionOrigin.OBSERVED, observed_provenance, raw
        ))
    elif re.search(r"\bsin\s+material(?:es)?\b|\bmateriales? (?:aparte|no incluidos?)\b", folded):
        materials_claims.append(DimensionClaim(
            False, DimensionOrigin.OBSERVED, observed_provenance, raw
        ))

    device_claims = []
    device = _explicit_device_scope(folded)
    if device:
        device_claims.append(DimensionClaim(
            device, DimensionOrigin.OBSERVED, observed_provenance, raw
        ))

    currency_claims = []
    normalized_currency = _known(_clean(row.get("currency")))
    if normalized_currency:
        currency_claims.append(DimensionClaim(
            normalized_currency.upper(), DimensionOrigin.OBSERVED,
            observed_provenance, f"currency={normalized_currency}",
        ))
    for currency in _explicit_currencies(folded):
        currency_claims.append(DimensionClaim(
            currency, DimensionOrigin.OBSERVED, observed_provenance, raw
        ))

    return EconomicEvidenceDimensions(
        provider_identity=resolve_dimension(*provider_claims),
        price_scope=resolve_dimension(*price_scope_claims),
        geography=resolve_dimension(*geography_claims),
        market_scope=resolve_dimension(*market_claims),
        commercial_context=resolve_dimension(*context_claims),
        bundle_status=resolve_dimension(*bundle_claims),
        hardware_included=resolve_dimension(*hardware_claims),
        materials_included=resolve_dimension(*materials_claims),
        device_scope=resolve_dimension(*device_claims),
        currency=resolve_dimension(*currency_claims),
    )


def _explicit_price_scope(text: str) -> str | None:
    if re.search(r"\bpor hora\b|\bla hora\b|\bhora(?:s)? de (?:servicio|soporte|trabajo)\b", text):
        return "PER_HOUR"
    if re.search(r"\bpor mes\b|\bal mes\b|\bmensual(?:mente)?\b|\babono mensual\b", text):
        return "PER_MONTH"
    if re.search(r"\bpor visita\b|\bcada visita\b", text):
        return "PER_VISIT"
    if re.search(r"\bpor (?:equipo|unidad|pc|notebook|camara)\b", text):
        return "PER_UNIT"
    if re.search(r"\bdesde\b|\ba partir de\b", text):
        return "LOWER_BOUND"
    if re.search(r"\bprecio total\b|\btotal(?: final)?\b", text):
        return "TOTAL"
    return None


def _explicit_commercial_context(text: str) -> str | None:
    if re.search(r"\burgenc(?:ia|ias)\b|\burgente\b", text):
        return "URGENCY"
    if re.search(r"\bfuera de horario\b|\bafter hours?\b", text):
        return "AFTER_HOURS"
    if re.search(r"\bfin(?:es)? de semana\b|\bferiado(?:s)?\b", text):
        return "WEEKEND_HOLIDAY"
    if re.search(r"\bpromocion\b|\bpromo\b", text):
        return "PROMOTION"
    if re.search(r"\bdescuento\b|\boff\b", text):
        return "DISCOUNT"
    if re.search(r"\bprecio (?:regular|estandar)\b|\btarifa estandar\b", text):
        return "STANDARD"
    return None


def _explicit_device_scope(text: str) -> str | None:
    for pattern, value in (
        (r"\bnotebooks?\b", "NOTEBOOK"),
        (r"\bpc gamer\b", "PC_GAMER"),
        (r"\b(?:pc|computadora)(?:s)?\b", "PC"),
        (r"\bservidores?\b", "SERVER"),
        (r"\bcamaras?\b", "CAMERA"),
        (r"\bimpresoras?\b", "PRINTER"),
    ):
        if re.search(pattern, text):
            return value
    return None


def _explicit_currencies(text: str) -> tuple[str, ...]:
    currencies = []
    if re.search(r"\bu\$s\b|\busd\b|\bdolares?\b", text):
        currencies.append("USD")
    if re.search(r"\bars\b|\bpesos?\b", text):
        currencies.append("ARS")
    return tuple(currencies)


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
