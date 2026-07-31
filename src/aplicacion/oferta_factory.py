from typing import Optional

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.dominio.empresa import Empresa
from src.dominio.normalizador_servicios import NormalizadorServicios
from src.dominio.oferta import Oferta
from src.normalizadores.normalizador_precios import NormalizadorPrecios


class OfertaFactory:
    """
    Fabrica entidades Oferta desde DTOs de aplicación.
    """

    def __init__(
        self,
        normalizador: Optional[NormalizadorServicios] = None,
    ):
        self.normalizador = normalizador or NormalizadorServicios()


    def crear_desde_dto(
        self,
        dto: OfertaDTO,
    ) -> Optional[Oferta]:

        empresa = Empresa(
            nombre=dto.empresa_nombre,
            provincia=dto.provincia,
            ciudad=dto.ciudad,
            fuente=dto.fuente,
        )


        servicio_canonico = self.normalizador.normalizar(
            dto.servicio_raw
        )

        if not servicio_canonico:
            return None


        precio = dto.precio
        moneda = dto.moneda


        # Compatibilidad con scrapers que entregan precio crudo
        precio_raw = getattr(
            dto,
            "precio_raw",
            None
        )

        if precio_raw and precio is None:

            precio_normalizado = (
                NormalizadorPrecios.normalizar(precio_raw)
            )

            precio = precio_normalizado.valor
            moneda = precio_normalizado.moneda


        return Oferta(
            empresa=empresa,
            servicio=servicio_canonico,
            precio=precio,
            moneda=moneda,
            fecha_relevamiento=dto.fecha_relevamiento,
        )


    # Compatibilidad histórica
    crear_oferta_desde_dto = crear_desde_dto