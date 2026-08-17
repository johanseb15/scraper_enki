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
        "parsed": {
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
            "clarification_required": parsed.metadata.clarification_required,
            "clarification_reason": parsed.metadata.clarification_reason,
            "clarification_question": parsed.metadata.clarification_question,
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
            "commercial_context": evidence.commercial_context,
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
