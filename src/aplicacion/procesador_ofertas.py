from datetime import date
from typing import List, Optional

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.oferta_factory import OfertaFactory
from src.dominio.oferta import Oferta
from src.normalizadores.normalizador_precios import NormalizadorPrecios


class ProcesadorOfertas:
    """
    Caso de uso encargado de transformar DTOs provenientes
    de scrapers en entidades Oferta del dominio.
    """

    def __init__(
        self,
        factory: Optional[OfertaFactory] = None,
        repositorio=None,
    ):
        self.factory = factory or OfertaFactory()
        self.repositorio = repositorio
        self.normalizador_precios = NormalizadorPrecios()

    def _normalizar_precio(self, dto: OfertaDTO) -> OfertaDTO:
        """
        Normaliza precios provenientes de scrapers.

        Soporta:
        - Precio ya normalizado:
            precio=25000

        - Precio crudo:
            precio_raw="$ 25.000 ARS"
        """

        precio = getattr(dto, "precio", None)
        moneda = getattr(dto, "moneda", "ARS")
        precio_raw = getattr(dto, "precio_raw", None)

        if precio is None and precio_raw:

            precio_normalizado = self.normalizador_precios.normalizar(
                precio_raw
            )

            precio = precio_normalizado.valor
            moneda = precio_normalizado.moneda

        return OfertaDTO(
            empresa_nombre=getattr(
                dto,
                "empresa_nombre",
                getattr(dto, "empresa", "")
            ),

            provincia=dto.provincia,

            ciudad=dto.ciudad,

            fuente=dto.fuente,

            servicio_raw=getattr(
                dto,
                "servicio_raw",
                getattr(dto, "servicio", "")
            ),

            precio=precio,

            precio_raw=precio_raw,

            moneda=moneda,

            fecha_relevamiento=getattr(
                dto,
                "fecha_relevamiento",
                None
            ),
        )

    def procesar(self, dto: OfertaDTO) -> Optional[Oferta]:
        """
        Procesa un DTO:
        1. Normaliza precio.
        2. Convierte a entidad Oferta.
        3. Persiste si existe repositorio.
        """

        dto_normalizado = self._normalizar_precio(dto)

        oferta = self.factory.crear_desde_dto(
            dto_normalizado
        )

        if oferta and self.repositorio:
            self.repositorio.guardar(oferta)

        return oferta

    def crear_oferta(
        self,
        dto: OfertaDTO,
        fecha_relevamiento: Optional[date] = None,
    ) -> Optional[Oferta]:
        """
        Crea una oferta desde un DTO recibido.

        Mantiene compatibilidad con DTOs antiguos:
        - empresa
        - servicio
        - precio_raw

        y DTOs actuales:
        - empresa_nombre
        - servicio_raw
        - precio
        """

        dto_adaptado = OfertaDTO(
            empresa_nombre=getattr(
                dto,
                "empresa_nombre",
                getattr(dto, "empresa", "")
            ),

            provincia=dto.provincia,

            ciudad=dto.ciudad,

            fuente=dto.fuente,

            servicio_raw=getattr(
                dto,
                "servicio_raw",
                getattr(dto, "servicio", "")
            ),

            precio=getattr(
                dto,
                "precio",
                None
            ),

            precio_raw=getattr(
                dto,
                "precio_raw",
                None
            ),

            moneda=getattr(
                dto,
                "moneda",
                "ARS"
            ),

            fecha_relevamiento=fecha_relevamiento,
        )

        return self.procesar(dto_adaptado)

    def ejecutar(
        self,
        dtos: List[OfertaDTO],
    ) -> List[Oferta]:
        """
        Procesa una lista completa de DTOs.
        """

        ofertas_procesadas = []

        for dto in dtos:

            oferta = self.procesar(dto)

            if oferta:
                ofertas_procesadas.append(oferta)

        return ofertas_procesadas