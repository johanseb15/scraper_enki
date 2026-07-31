from abc import ABC, abstractmethod

from src.aplicacion.dto.oferta_dto import OfertaDTO


class BaseScraper(ABC):
    """Contrato base para todos los scrapers de empresas IT."""

    @abstractmethod
    def obtener_servicios(self) -> list[OfertaDTO]:
        """Obtiene y normaliza los servicios de una fuente en forma de DTOs."""
        pass
