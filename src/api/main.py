from __future__ import annotations

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.aplicacion.enki_pricing_query_service import resolver_consulta_pricing
from src.aplicacion.enki_pricing_response import presentar_resultado_pricing
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing_runtime
from src.aplicacion.pricing_evidence_engine import CohortePricing
from src.configuracion_runtime import resolver_ruta_db_ofertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.normalizadores.normalizador_servicios import NormalizadorServicios
from src.reporte import generar_resumen_servicio
from src.dominio.commercial_context import serialize_commercial_context


app = FastAPI(title="Enki API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DecisionPricingRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


def obtener_repositorio() -> RepositorioSQLiteOfertas:
    return RepositorioSQLiteOfertas(ruta_db=resolver_ruta_db_ofertas())


def obtener_cohortes_pricing() -> tuple[list[CohortePricing], list[CohortePricing]]:
    return cargar_cohortes_pricing_runtime()


def _serialize_market_resolution(market_resolution):
    if market_resolution is None:
        return None
    return {
        "clarification_required": market_resolution.clarification_required,
        "clarification_reason": market_resolution.clarification_reason,
        "clarification_question": market_resolution.clarification_question,
        "resolutions": [
            {
                "route": item.route,
                "status": item.status,
                "canonical_service": item.canonical_service,
                "economic_object_kind": item.economic_object_kind,
                "market_scope": item.market_scope,
                "market": item.market,
                "market_key": item.market_key,
                "market_status": item.market_status,
                "resolution_reason": item.resolution_reason,
            }
            for item in market_resolution.resolutions
        ],
    }


def _serialize_pricing_readiness(pricing_readiness):
    if pricing_readiness is None:
        return None

    def serialize_route(item):
        return {
            "route": item.route,
            "status": item.status,
            "ready": item.ready,
            "canonical_service": item.canonical_service,
            "market_scope": item.market_scope,
            "market": item.market,
            "market_key": item.market_key,
            "reason": item.reason,
            "pricing_status": item.pricing_status,
        }

    return {
        "routes": [serialize_route(item) for item in pricing_readiness.routes],
        "ready_routes": [serialize_route(item) for item in pricing_readiness.ready_routes],
        "blocked_routes": [serialize_route(item) for item in pricing_readiness.blocked_routes],
    }


def _serialize_evidence_probe(evidence_probe):
    if evidence_probe is None:
        return None
    return {
        "probes": [
            {
                "route": item.route,
                "status": item.status,
                "market": item.market,
                "canonical_service": item.canonical_service,
                "observations_n": item.observations_n,
                "providers_n": item.providers_n,
                "evidence_confidence": item.evidence_confidence,
                "observed_min": item.observed_min,
                "observed_max": item.observed_max,
                "median": item.median,
                "reason": item.reason,
            }
            for item in evidence_probe.probes
        ],
    }

def _serialize_decision_result(result):
    parsed = result.parsed
    response = presentar_resultado_pricing(result)
    evidence = result.evidence

    return {
        "status": result.status,
        "headline": response.headline,
        "summary": response.summary,
        "evidence_line": response.evidence_line,
        "caveat": response.caveat,
        "clarification_reason": result.clarification_reason,
        "clarification_question": result.clarification_question,
        "unsupported_reason": result.unsupported_reason,
        "market_resolution": _serialize_market_resolution(result.market_resolution),
        "pricing_readiness": _serialize_pricing_readiness(result.pricing_readiness),
        "evidence_probe": _serialize_evidence_probe(result.evidence_probe),
        "parsed": {
            "query_kind": parsed.query_kind.value,
            "intent_action": parsed.intent_action.value,
            "intent_side": parsed.intent_side.value,
            "economic_object_kind": parsed.economic_object_kind.value,
            "canonical_services": list(parsed.canonical_services),
            "market_scope": parsed.market_scope.value,
            "modality": parsed.modality.value,
            "price": {
                "type": parsed.price.type.value,
                "value": parsed.price.value,
                "min": parsed.price.min,
                "max": parsed.price.max,
                "currency": parsed.price.currency,
                "is_approximate": parsed.price.is_approximate,
            },
            "geography": {
                "province": parsed.geography.province,
                "city": parsed.geography.city,
            },
            "device_type": parsed.device_type,
            "condition": parsed.condition,
            "is_bundle": parsed.is_bundle,
            "parts_scope": parsed.commercial_context.parts_scope.value,
            "commercial_context": serialize_commercial_context(
                parsed.commercial_context
            ),
            "clarification_required": parsed.metadata.clarification_required,
            "clarification_reason": parsed.metadata.clarification_reason,
            "clarification_question": parsed.metadata.clarification_question,
            "technical_need": None if parsed.technical_need is None else {
                "domain": parsed.technical_need.domain,
                "technical_problem": parsed.technical_need.technical_problem,
                "economic_intent_explicit": parsed.technical_need.economic_intent_explicit,
                "candidate_routes": list(parsed.technical_need.candidate_routes),
                "product_purchase_recommendation": parsed.technical_need.product_purchase_recommendation,
                "clarification_required": parsed.technical_need.clarification_required,
            },
        },
        "evidence": None if evidence is None else {
            "market": evidence.market,
            "canonical_service": evidence.canonical_service,
            "observations_n": evidence.observations_n,
            "providers_n": evidence.providers_n,
            "min_ars": evidence.min_ars,
            "q1_ars": evidence.q1_ars,
            "median_ars": evidence.median_ars,
            "q3_ars": evidence.q3_ars,
            "max_ars": evidence.max_ars,
            "evidence_confidence": evidence.evidence_confidence,
            "price_position": evidence.price_position,
            "decision_label": evidence.decision_label,
            "price_scope": evidence.price_scope,
            "commercial_context": evidence.commercial_context.value.value,
            "commercial_context_provenance": serialize_commercial_context(
                evidence.commercial_context
            ),
            "evidence_commercial_context": None
            if evidence.evidence_commercial_context is None
            else serialize_commercial_context(evidence.evidence_commercial_context),
            "lineage_gate_version": evidence.lineage_gate_version,
            "service_reach_gate_version": evidence.service_reach_gate_version,
            "temporal_gate_version": evidence.temporal_gate_version,
            "temporal_state": evidence.temporal_state,
            "acquired_at_min": evidence.acquired_at_min,
            "acquired_at_max": evidence.acquired_at_max,
            "freshness_policy_version": evidence.freshness_policy_version,
            "observation_ids": list(evidence.observation_ids),
        },
    }


@app.post("/decision/pricing")
def decision_pricing(
    payload: DecisionPricingRequest,
    cohortes: tuple[list[CohortePricing], list[CohortePricing]] = Depends(obtener_cohortes_pricing),
):
    local_cohortes, remote_cohortes = cohortes
    result = resolver_consulta_pricing(
        payload.query,
        local_cohortes=local_cohortes,
        remote_cohortes=remote_cohortes,
    )
    return _serialize_decision_result(result)


@app.get("/servicios/{nombre_servicio}")
def consultar_servicio(
    nombre_servicio: str,
    provincia: str | None = Query(default=None),
    ciudad: str | None = Query(default=None),
    repo: RepositorioSQLiteOfertas = Depends(obtener_repositorio),
):
    servicios = repo.obtener_todas()
    servicio_canonico = NormalizadorServicios().normalizar(nombre_servicio)

    servicios_filtrados = [
        servicio for servicio in servicios if servicio.servicio == servicio_canonico
    ]

    if provincia:
        servicios_filtrados = [
            servicio
            for servicio in servicios_filtrados
            if (servicio.empresa.provincia or "").lower() == provincia.lower()
        ]

    if ciudad:
        servicios_filtrados = [
            servicio
            for servicio in servicios_filtrados
            if (servicio.empresa.ciudad or "").lower() == ciudad.lower()
        ]

    resumen = generar_resumen_servicio(servicios_filtrados, nombre_servicio)

    resumen["empresas"] = [
        {"empresa": servicio.empresa.nombre, "precio": servicio.precio}
        for servicio in servicios_filtrados
    ]

    resumen["ciudades"] = sorted({
        servicio.empresa.ciudad
        for servicio in servicios_filtrados
        if servicio.empresa.ciudad
    })

    resumen["provincias"] = sorted({
        servicio.empresa.provincia
        for servicio in servicios_filtrados
        if servicio.empresa.provincia
    })

    return resumen
