from datetime import date
from typing import List, Optional

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.oferta_factory import OfertaFactory
from src.dominio.oferta import Oferta, PrecioValor
from src.normalizadores.normalizador_empresas import NormalizadorEmpresas
from src.normalizadores.normalizador_precios import NormalizadorPrecios
from src.normalizadores.normalizador_ubicaciones import NormalizadorUbicaciones


class ProcesadorOfertas:
    """Orquesta la normalizacion de DTOs y su ingreso al dominio."""

    def __init__(
        self,
        factory: Optional[OfertaFactory] = None,
        repositorio=None,
        normalizador_ubicaciones=None,
        normalizador_empresas=None,
        normalizador_servicios=None,
    ):
        self.factory = factory or OfertaFactory(normalizador=normalizador_servicios)
        self.repositorio = repositorio
        self.normalizador_ubicaciones = (
            normalizador_ubicaciones or NormalizadorUbicaciones()
        )
        self.normalizador_empresas = normalizador_empresas or NormalizadorEmpresas()

    def procesar(self, dto: OfertaDTO) -> Optional[Oferta]:
        dto_normalizado = self._normalizar_datos(dto)

        if not dto_normalizado.servicio_raw:
            return None

        oferta = self.factory.crear_desde_dto(dto_normalizado)

        if oferta and self.repositorio:
            self.repositorio.guardar(oferta)

        return oferta

    def crear_oferta(
        self,
        dto: OfertaDTO,
        fecha_relevamiento: Optional[date] = None,
    ) -> Optional[Oferta]:
        """Alias legacy; la fecha vigente pertenece al propio DTO."""
        return self.procesar(dto)

    def crear_ofertas(self, dto: OfertaDTO) -> List[Oferta]:
        dto_normalizado = self._normalizar_datos(dto)

        if not dto_normalizado.servicio_raw:
            return []

        precios_por_modalidad = (
            ("freelance", dto_normalizado.precio_freelance_raw),
            ("local", dto_normalizado.precio_local_raw),
        )
        tiene_precios_por_modalidad = any(
            precio_raw for _, precio_raw in precios_por_modalidad
        )

        if not tiene_precios_por_modalidad:
            oferta = self.factory.crear_desde_dto(dto_normalizado)
            ofertas = [oferta] if oferta else []
        else:
            ofertas = []
            for modalidad, precio_raw in precios_por_modalidad:
                if not precio_raw:
                    continue

                precio_normalizado = NormalizadorPrecios.normalizar(precio_raw)
                if precio_normalizado.valor <= 0:
                    continue

                oferta = self.factory.crear_desde_dto(
                    dto_normalizado,
                    precio_normalizado=precio_normalizado,
                    modalidad=modalidad,
                    precio_raw=precio_raw,
                )
                if oferta:
                    ofertas.append(oferta)

        if self.repositorio:
            for oferta in ofertas:
                self.repositorio.guardar(oferta)

        return ofertas

    def ejecutar(self, dtos: List[OfertaDTO]) -> List[Oferta]:
        ofertas = []

        for dto in dtos:
            ofertas.extend(self.crear_ofertas(dto))

        return ofertas

    @staticmethod
    def _obtener_empresa_raw(dto: OfertaDTO) -> str:
        return getattr(dto, "empresa_nombre", None) or getattr(dto, "empresa", "")

    @staticmethod
    def _obtener_servicio_raw(dto: OfertaDTO) -> str:
        return getattr(dto, "servicio_raw", None) or getattr(dto, "servicio", "")

    def _normalizar_datos(self, dto: OfertaDTO) -> OfertaDTO:
        ubicacion = self.normalizador_ubicaciones.normalizar(
            provincia=dto.provincia,
            ciudad=dto.ciudad,
        )
        empresa = self.normalizador_empresas.normalizar(
            self._obtener_empresa_raw(dto)
        )
        precio = getattr(dto, "precio", None)

        if precio is None:
            precio_raw = getattr(dto, "precio_raw", None)
            if precio_raw:
                precio_normalizado = NormalizadorPrecios.normalizar(precio_raw)
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
            servicio_raw=self._obtener_servicio_raw(dto),
            equipo_raw=getattr(dto, "equipo_raw", ""),
            precio=precio,
            moneda=dto.moneda,
            fecha_relevamiento=getattr(dto, "fecha_relevamiento", None),
            precio_raw=getattr(dto, "precio_raw", None),
            precio_freelance_raw=getattr(dto, "precio_freelance_raw", None),
            precio_local_raw=getattr(dto, "precio_local_raw", None),
        )
