from dataclasses import dataclass
from datetime import date

from src.dominio.empresa import Empresa
from src.dominio.servicios import ServicioCanonico


@dataclass(frozen=True)
class Oferta:
    empresa: Empresa
    servicio: ServicioCanonico
    precio: int
    moneda: str
    fecha_relevamiento: date
