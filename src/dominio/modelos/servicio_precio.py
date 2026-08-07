from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(slots=True)
class ServicioPrecio:
    servicio: str = ""

    precio: float = 0.0
    precio_freelance: float = 0.0
    precio_local: float = 0.0

    moneda: str = "ARS"

    empresa: Optional[str] = None

    provincia: Optional[str] = None
    ciudad: Optional[str] = None
    ubicacion: Optional[str] = None

    equipo: Optional[str] = None

    url: Optional[str] = None
    fuente: Optional[str] = None

    fecha_relevamiento: Optional[date] = None

    @property
    def proveedor(self) -> Optional[str]:
        """Alias de compatibilidad con el repositorio."""
        return self.empresa

    @property
    def titulo(self) -> str:
        """Alias utilizado por algunos componentes legacy."""
        return self.servicio