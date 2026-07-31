from dataclasses import dataclass


@dataclass(frozen=True)
class Ubicacion:
    provincia: str
    ciudad: str