from typing import Optional
from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.dominio.empresa import Empresa
from src.dominio.normalizador_servicios import NormalizadorServicios
from src.dominio.oferta import Oferta


class OfertaFactory:
    """Fábrica encargada de instanciar entidades Oferta a partir de DTOs de entrada."""

    def __init__(self, normalizador: Optional[NormalizadorServicios] = None):
        self.normalizador = normalizador or NormalizadorServicios()

    def crear_desde_dto(self, dto: OfertaDTO) -> Optional[Oferta]:
        # Compatibilidad con atributos de empresa según el DTO
        empresa_nombre = getattr(dto, "empresa", getattr(dto, "empresa_nombre", ""))
        fuente = getattr(dto, "fuente", "")

        empresa = Empresa(
            nombre=empresa_nombre,
            provincia=dto.provincia,
            ciudad=dto.ciudad,
            fuente=fuente,
        )

        servicio_raw = getattr(dto, "servicio", getattr(dto, "servicio_raw", ""))
        servicio_canonico = self.normalizador.normalizar(servicio_raw)

        # Si el servicio no puede normalizarse o mapearse, se maneja de forma resiliente
        if not servicio_canonico:
            return None

        # src/aplicacion/oferta_factory.py (línea ~33)

        return Oferta(
            empresa=empresa,
            servicio=servicio_canonico,
            precio=dto.precio,
            moneda=dto.moneda,
            
            fecha_relevamiento=getattr(dto, "fecha_relevamiento", None),
        )

    # Alias para compatibilidad
    crear_oferta_desde_dto = crear_desde_dto