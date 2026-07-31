from datetime import date
from typing import List, Optional
from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.oferta_factory import OfertaFactory
from src.dominio.oferta import Oferta


class ProcesadorOfertas:
    """Coordinador de aplicación para transformar DTOs en entidades de dominio

    y llevar a cabo su persistencia.
    """

    def __init__(self, factory: Optional[OfertaFactory] = None, repositorio=None):
        self.factory = factory or OfertaFactory()
        self.repositorio = repositorio

    def procesar(self, dto: OfertaDTO) -> Optional[Oferta]:
        """Procesa un único DTO, lo convierte en Oferta y lo guarda si hay repositorio configurado."""
        if hasattr(self.factory, "crear_desde_dto"):
            oferta = self.factory.crear_desde_dto(dto)
        elif hasattr(self.factory, "crear_oferta_desde_dto"):
            oferta = self.factory.crear_oferta_desde_dto(dto)
        else:
            raise AttributeError(
                "OfertaFactory no implementa 'crear_desde_dto' ni 'crear_oferta_desde_dto'"
            )

        if oferta and self.repositorio:
            self.repositorio.guardar(oferta)

        return oferta

    def crear_oferta(
        self, dto: OfertaDTO, fecha_relevamiento: Optional[date] = None
    ) -> Optional[Oferta]:
        """Crea una oferta desde un DTO actualizando la fecha de relevamiento si se provee."""
        if fecha_relevamiento is not None:
            try:
                dto.fecha_relevamiento = fecha_relevamiento
            except AttributeError:
                pass
        return self.procesar(dto)

    def ejecutar(self, dtos: List[OfertaDTO]) -> List[Oferta]:
        """Procesa una lista completa de DTOs y retorna las ofertas creadas exitosamente."""
        ofertas_procesadas: List[Oferta] = []
        for dto in dtos:
            oferta = self.procesar(dto)
            if oferta:
                ofertas_procesadas.append(oferta)
        return ofertas_procesadas
