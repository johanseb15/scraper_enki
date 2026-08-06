from dataclasses import dataclass


@dataclass(frozen=True)
class Precio:
    monto: float
    moneda: str = "ARS"