from datetime import date
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico
from src.dominio.normalizador_servicios import NormalizadorServicios
from src.aplicacion.dtos import OfertaDTO
from src.aplicacion.factories import OfertaFactory


class ProcesadorOfertas:

    def __init__(self):
        self.normalizador = NormalizadorServicios()
        self.factory = OfertaFactory()

    def crear_oferta(self, dto: OfertaDTO, fecha_relevamiento: date) -> Oferta:
        # 1. Interpretación semántica (Responsabilidad del Caso de Uso)
        try:
            servicio_canonico = self.normalizador.normalizar(dto.servicio)
        except Exception:
            servicio_canonico = getattr(ServicioCanonico, "DESCONOCIDO", list(ServicioCanonico)[0])

        # Si el normalizador devuelve None o un valor no mapeado, aseguramos el fallback a DESCONOCIDO
        if servicio_canonico is None:
            servicio_canonico = getattr(ServicioCanonico, "DESCONOCIDO", list(ServicioCanonico)[0])

        # 2. Ensamblado de la entidad a través de la factoría pura
        return self.factory.crear(dto, servicio_canonico, fecha_relevamiento)