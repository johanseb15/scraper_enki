from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.dominio.empresa import Empresa
from src.dominio.servicios import ServicioCanonico


class PrecioValor(Decimal):
    def __new__(cls, valor, moneda: str = "ARS", periodo: str | None = None, raw: str | None = None):
        instancia = super().__new__(cls, str(valor))
        instancia.valor = Decimal(str(valor))
        instancia.moneda = moneda
        instancia.periodo = periodo
        instancia.raw = raw
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
