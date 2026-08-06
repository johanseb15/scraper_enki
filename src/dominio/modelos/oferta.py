from dataclasses import dataclass
from src.dominio.servicios import ServicioCanonico


@dataclass(frozen=True)
class Oferta:
    titulo: str
    precio: float
    moneda: str
    servicio: ServicioCanonico
    proveedor: str
    url: str