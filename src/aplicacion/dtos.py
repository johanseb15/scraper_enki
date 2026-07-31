from dataclasses import dataclass


@dataclass(frozen=True)
class OfertaDTO:
    empresa: str
    provincia: str
    ciudad: str
    servicio: str
    precio: int
    moneda: str
    fuente: str
