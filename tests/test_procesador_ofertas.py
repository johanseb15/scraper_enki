from datetime import date
from typing import List, Optional

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.oferta_factory import OfertaFactory
from src.dominio.oferta import Oferta
from src.dominio.normalizador_ubicaciones import NormalizadorUbicaciones
from src.normalizadores.normalizador_precios import NormalizadorPrecios


class ProcesadorOfertas:
    """
    Coordinador de aplicación encargado de transformar DTOs crudos
    en entidades Oferta válidas del dominio.
    """

    def __init__(
        self,
        factory: Optional[OfertaFactory] = None,
        repositorio=None,
        normalizador_ubicaciones: Optional[NormalizadorUbicaciones] = None,
    ):
        self.factory = factory or OfertaFactory()
        self.repositorio = repositorio
        self.normalizador_ubicaciones = (
            normalizador_ubicaciones or NormalizadorUbicaciones()
        )

    def procesar(self, dto: OfertaDTO) -> Optional[Oferta]:
        dto_normalizado = self._normalizar_datos(dto)

        oferta = self.factory.crear_desde_dto(dto_normalizado)

        if oferta and self.repositorio:
            self.repositorio.guardar(oferta)

        return oferta

    def crear_oferta(
        self,
        dto: OfertaDTO,
        fecha_relevamiento: Optional[date] = None,
    ) -> Optional[Oferta]:

        if fecha_relevamiento:
            try:
                dto.fecha_relevamiento = fecha_relevamiento
            except AttributeError:
                pass

        return self.procesar(dto)

    def ejecutar(
        self,
        dtos: List[OfertaDTO],
    ) -> List[Oferta]:

        ofertas = []

        for dto in dtos:
            oferta = self.procesar(dto)

            if oferta:
                ofertas.append(oferta)

        return ofertas

    def _normalizar_datos(self, dto: OfertaDTO) -> OfertaDTO:
        """
        Aplica transformaciones ETL sobre datos de entrada.
        """

        ubicacion = self.normalizador_ubicaciones.normalizar(
            provincia=dto.provincia,
            ciudad=dto.ciudad,
        )

        dto_normalizado = OfertaDTO(
            empresa_nombre=getattr(
                dto,
                "empresa_nombre",
                getattr(dto, "empresa", "")
            ),
            provincia=ubicacion.provincia,
            ciudad=ubicacion.ciudad,
            fuente=dto.fuente,
            servicio_raw=getattr(
                dto,
                "servicio_raw",
                getattr(dto, "servicio", "")
            ),
            precio=getattr(dto, "precio", None),
            moneda=dto.moneda,
            fecha_relevamiento=getattr(
                dto,
                "fecha_relevamiento",
                None
            ),
        )

        if dto_normalizado.precio is None:
            precio_raw = getattr(dto, "precio_raw", None)

            if precio_raw:
                precio = NormalizadorPrecios.normalizar(precio_raw)

                dto_normalizado = OfertaDTO(
                    empresa_nombre=dto_normalizado.empresa_nombre,
                    provincia=dto_normalizado.provincia,
                    ciudad=dto_normalizado.ciudad,
                    fuente=dto_normalizado.fuente,
                    servicio_raw=dto_normalizado.servicio_raw,
                    precio=precio.valor,
                    moneda=precio.moneda,
                    fecha_relevamiento=dto_normalizado.fecha_relevamiento,
                )

        return dto_normalizado