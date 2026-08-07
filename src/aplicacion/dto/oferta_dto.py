from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True, init=False)
class OfertaDTO:
    """
    DTO de transporte entre scrapers y aplicación.

    Contrato:
    - Los scrapers entregan datos crudos.
    - La aplicación normaliza.
    - El dominio recibe entidades limpias.

    Compatibilidad:
        formato antiguo:
            empresa
            servicio
            precio_raw

        formato nuevo:
            empresa_nombre
            servicio_raw
            precio
    """

    empresa_nombre: str
    provincia: str
    ciudad: str
    fuente: str

    servicio_raw: str
    equipo_raw: str

    precio: Optional[int]
    moneda: str

    fecha_relevamiento: Optional[date]

    precio_raw: Optional[str]
    precio_freelance_raw: Optional[str]
    precio_local_raw: Optional[str]


    def __init__(
        self,
        empresa=None,
        provincia="",
        ciudad="",
        servicio=None,
        precio=None,
        moneda="ARS",
        fuente="",
        precio_raw=None,
        empresa_nombre=None,
        servicio_raw=None,
        fecha_relevamiento=None,
        equipo_raw="",
        precio_freelance_raw=None,
        precio_local_raw=None,
    ):

        object.__setattr__(
            self,
            "empresa_nombre",
            empresa_nombre or empresa or ""
        )

        object.__setattr__(
            self,
            "provincia",
            provincia
        )

        object.__setattr__(
            self,
            "ciudad",
            ciudad
        )

        object.__setattr__(
            self,
            "fuente",
            fuente
        )

        object.__setattr__(
            self,
            "servicio_raw",
            servicio_raw or servicio or ""
        )

        object.__setattr__(
            self,
            "equipo_raw",
            equipo_raw
        )

        object.__setattr__(
            self,
            "precio",
            precio
        )

        object.__setattr__(
            self,
            "moneda",
            moneda
        )

        object.__setattr__(
            self,
            "precio_raw",
            precio_raw
        )

        object.__setattr__(
            self,
            "precio_freelance_raw",
            precio_freelance_raw
        )

        object.__setattr__(
            self,
            "precio_local_raw",
            precio_local_raw
        )

        object.__setattr__(
            self,
            "fecha_relevamiento",
            fecha_relevamiento
        )


    @property
    def empresa(self):
        """
        Compatibilidad legacy.
        """
        return self.empresa_nombre


    @property
    def servicio(self):
        """
        Compatibilidad legacy.

        Si el valor almacenado corresponde a un ServicioCanonico,
        lo reconstruye automáticamente.

        Si no pertenece al dominio, devuelve el texto original.
        """

        from src.dominio.servicios import ServicioCanonico

        valor = self.servicio_raw

        if isinstance(valor, ServicioCanonico):
            return valor

        if isinstance(valor, str):
            try:
                return ServicioCanonico(valor)
            except ValueError:
                return valor

        return valor
