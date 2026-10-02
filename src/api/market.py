import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, model_validator

from src.aplicacion.market_query_service import query_market
from src.dominio.catalogos.servicios import CatalogoServicios
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.demo_evidence_repository import (
    DEFAULT_MANIFEST, load_demo_evidence, verified_captures,
)


router = APIRouter(prefix="/market", tags=["Demo comercial"])
logger = logging.getLogger(__name__)


class MarketRequest(BaseModel):
    service: Literal["malware","formateo","mantenimiento","soporte_redes","soporte_tecnico"]
    province: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    currency: Literal["ARS","USD"] | None = None
    modality: str | None = Field(default=None, max_length=100)
    own_price: str | None = Field(default=None, max_length=40, strict=True)
    own_currency: Literal["ARS","USD"] = "ARS"
    own_unit: str | None = Field(default=None, max_length=100)
    own_scope: str | None = Field(default=None, max_length=300)
    own_modality: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def own_context(self):
        if self.own_price is not None and not all([self.own_unit,self.own_scope,self.own_modality]):
            raise ValueError("Seleccioná el alcance, la unidad y la modalidad de tu precio.")
        return self


def observations():
    try:
        return load_demo_evidence()
    except (ValueError,OSError,KeyError) as exc:
        logger.error("Evidencia demo inválida: %s", exc)
        raise HTTPException(503,"No se pudo verificar la evidencia guardada. Revisá las capturas y sus hashes.") from exc


@router.get("/catalog")
def catalog():
    items = observations()
    catalog = CatalogoServicios()
    services = [catalog.obtener_por_canonico(s) for s in ServicioCanonico]
    return {"services":[{"id":s.id.value,"label":s.nombre_display,"category":s.categoria}
                        for s in services if s],
            "provinces": sorted({o.province for o in items if o.province}),
            "cities": sorted({o.city for o in items if o.city}),
            "currencies": sorted({o.currency for o in items if o.currency}),
            "modalities": sorted({o.modality for o in items if o.modality}),
            "capture_count":len({o.capture_id for o in items}),
            "observation_count":len(items)}


@router.post("/query")
def market_query(payload: MarketRequest):
    try:
        return query_market(observations(),**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc


@router.get("/captures/{capture_id}", response_class=PlainTextResponse)
def capture(capture_id: str):
    try:
        _, captures = verified_captures(DEFAULT_MANIFEST)
    except (ValueError,OSError,KeyError) as exc:
        raise HTTPException(503,"No se pudo verificar la evidencia guardada.") from exc
    c = captures.get(capture_id)
    if c is None:
        raise HTTPException(404,"Captura no encontrada")
    # HTML servido como texto: conserva la evidencia sin ejecutar scripts de terceros.
    return PlainTextResponse(f"ENKI · Captura pública guardada\nFuente: {c['source_url']}\n"
        f"Capturada: {c['captured_at']}\nsha256: {c['sha256']}\n"
        "Esta fecha corresponde a la captura, no a la vigencia del precio.\n\n"
        + c["content"].decode("utf-8"),headers={"X-Content-Type-Options":"nosniff"})
