from dataclasses import dataclass
from typing import Optional


@dataclass
class ServicioPrecio:
    servicio: str = ""
    precio: float = 0.0
    moneda: str = "ARS"
    empresa: Optional[str] = None
    ubicacion: Optional[str] = None
    url: Optional[str] = None