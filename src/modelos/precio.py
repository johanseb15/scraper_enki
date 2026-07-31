from dataclasses import dataclass


@dataclass(frozen=True)
class Precio:
    valor: int
    moneda: str
    periodo: str | None = None
