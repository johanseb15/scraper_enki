from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ServicioPrecio:
    empresa: str
    provincia: str
    ciudad: str
    servicio: str
    equipo: str

    precio_freelance: int
    precio_local: int

    moneda: str

    fecha_relevamiento: date

    fuente: str