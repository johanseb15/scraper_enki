from dataclasses import dataclass


@dataclass(frozen=True)
class RechazoIngesta:
    fuente: str
    razon: str
