from datetime import date
from typing import List, Optional

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.oferta_factory import OfertaFactory

from src.dominio.oferta import Oferta, PrecioValor

from src.normalizadores.normalizador_ubicaciones import (
    NormalizadorUbicaciones,
)

from src.normalizadores.normalizador_empresas import (
    NormalizadorEmpresas,
)

from src.normalizadores.normalizador_precios import (
    NormalizadorPrecios,
)


class ProcesadorOfertas:
    """
    Orquestador de aplicación.

    Responsabilidad:
    - recibir DTO crudo
    - aplicar normalización ETL
    - entregar contrato limpio al dominio
    """

    def __init__(
        self,
        factory: Optional[OfertaFactory] = None,
        repositorio=None,
        normalizador_ubicaciones=None,
        normalizador_empresas=None,
    ):

        self.factory = factory or OfertaFactory()

        self.repositorio = repositorio

        self.normalizador_ubicaciones = (
            normalizador_ubicaciones
            or NormalizadorUbicaciones()
        )

        self.normalizador_empresas = (
            normalizador_empresas
            or NormalizadorEmpresas()
        )

    def procesar(
        self,
        dto: OfertaDTO,
    ) -> Optional[Oferta]:

        dto_normalizado = self._normalizar_datos(dto)

        if not dto_normalizado.servicio_raw:
            return None

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
        Método legacy.

        El parámetro fecha_relevamiento se mantiene por
        compatibilidad, pero el pipeline utiliza únicamente
        la fecha contenida dentro del DTO.
        """

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

    def _obtener_empresa_raw(
        self,
        dto: OfertaDTO,
    ) -> str:
        """
        Compatibilidad DTO legacy.
        """

        empresa = getattr(
            dto,
            "empresa_nombre",
            None,
        )

        if empresa:
            return empresa

        return getattr(
            dto,
            "empresa",
            "",
        )

    def _obtener_servicio_raw(
        self,
        dto: OfertaDTO,
    ) -> str:

        servicio = getattr(
            dto,
            "servicio_raw",
            None,
        )

        if servicio:
            return servicio

        return getattr(
            dto,
            "servicio",
            "",
        )

    def _normalizar_datos(
        self,
        dto: OfertaDTO,
    ) -> OfertaDTO:

        ubicacion = (
            self.normalizador_ubicaciones.normalizar(
                provincia=dto.provincia,
                ciudad=dto.ciudad,
            )
        )

        empresa = (
            self.normalizador_empresas.normalizar(
                self._obtener_empresa_raw(dto)
            )
        )

        servicio = self._obtener_servicio_raw(dto)

        precio = getattr(
            dto,
            "precio",
            None,
        )

        if precio is None:

            precio_raw = getattr(
                dto,
                "precio_raw",
                None,
            )

            if precio_raw:

                precio_normalizado = (
                    NormalizadorPrecios.normalizar(
                        precio_raw
                    )
                )

                precio = PrecioValor(
                    valor=precio_normalizado.valor,
                    moneda=precio_normalizado.moneda,
                    periodo=precio_normalizado.periodo,
                )

        return OfertaDTO(
            empresa_nombre=empresa,
            provincia=ubicacion.provincia,
            ciudad=ubicacion.ciudad,
            fuente=dto.fuente,
            servicio_raw=servicio,
            precio=precio,
            moneda=dto.moneda,
            fecha_relevamiento=getattr(
                dto,
                "fecha_relevamiento",
                None,
            ),
            precio_raw=getattr(
                dto,
                "precio_raw",
                None,
            ),
        )