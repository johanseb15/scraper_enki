from abc import ABC, abstractmethod
from typing import List
from src.aplicacion.dto.oferta_dto import OfertaDTO


class BaseScraper(ABC):
    @abstractmethod
    def obtener_servicios(self) -> List[OfertaDTO]:
        pass