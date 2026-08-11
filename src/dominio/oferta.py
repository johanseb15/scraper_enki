from dataclasses import dataclass
from datetime import date

from src.dominio.empresa import Empresa
from src.dominio.servicios import ServicioCanonico


class PrecioValor(int):
    def __new__(cls, valor: int, moneda: str = "ARS", periodo: str | None = None):
        instancia = super().__new__(cls, valor)
        instancia.valor = valor
        instancia.moneda = moneda
        instancia.periodo = periodo
        return instancia


@dataclass(frozen=True)
class Oferta:
    empresa: Empresa
    servicio: ServicioCanonico
    precio: PrecioValor
    moneda: str
    fecha_relevamiento: date
    servicio_raw: str = ""
    modalidad: str | None = None
    precio_raw: str | None = None
