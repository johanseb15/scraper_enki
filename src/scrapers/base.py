from abc import ABC, abstractmethod
from src.modelos.servicio_precio import ServicioPrecio


class BaseScraper(ABC):
    """Contrato base para todos los scrapers de empresas IT."""

    @abstractmethod
    def obtener_servicios(self) -> list[ServicioPrecio]:
        """Obtiene y normaliza los servicios de una fuente."""
        pass
