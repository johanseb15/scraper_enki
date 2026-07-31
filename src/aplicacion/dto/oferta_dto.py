from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class OfertaDTO:
    """Data Transfer Object que transporta la oferta cruda extraída

    por los scrapers hacia el ProcesadorOfertas en el Dominio.
    """

    empresa_nombre: str
    provincia: str
    ciudad: str
    fuente: str
    servicio_raw: str
    precio: int
    moneda: str = "ARS"
    fecha_relevamiento: Optional[date] = None
