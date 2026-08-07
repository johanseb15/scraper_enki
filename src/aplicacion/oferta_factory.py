from typing import Optional

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta, PrecioValor
from src.normalizadores.normalizador_precios import NormalizadorPrecios
from src.normalizadores.normalizador_servicios import NormalizadorServicios


class OfertaFactory:
    """Crea la entidad de dominio oficial a partir del DTO del pipeline."""

    def __init__(self, normalizador: Optional[NormalizadorServicios] = None):
        self.normalizador = normalizador or NormalizadorServicios()

    def crear_desde_dto(
        self,
        dto: OfertaDTO,
        precio_normalizado=None,
        modalidad: Optional[str] = None,
        precio_raw: Optional[str] = None,
    ) -> Optional[Oferta]:
        servicio_canonico = self.normalizador.normalizar(dto.servicio_raw)
        if not servicio_canonico:
            return None

        empresa = Empresa(
            nombre=dto.empresa_nombre,
            provincia=dto.provincia,
            ciudad=dto.ciudad,
            fuente=dto.fuente,
        )

        precio = dto.precio if precio_normalizado is None else precio_normalizado
        moneda = dto.moneda

        if isinstance(precio, PrecioValor):
            moneda = precio.moneda
        elif isinstance(precio, int) and not isinstance(precio, bool):
            precio = PrecioValor(valor=precio, moneda=moneda)
        elif precio is not None and hasattr(precio, "valor"):
            moneda = getattr(precio, "moneda", moneda)
            precio = PrecioValor(
                valor=precio.valor,
                moneda=moneda,
                periodo=getattr(precio, "periodo", None),
            )

        if precio is None and dto.precio_raw:
            precio_normalizado = NormalizadorPrecios.normalizar(dto.precio_raw)
            precio = PrecioValor(
                valor=precio_normalizado.valor,
                moneda=precio_normalizado.moneda,
                periodo=precio_normalizado.periodo,
            )
            moneda = precio.moneda

        return Oferta(
            empresa=empresa,
            servicio=servicio_canonico,
            precio=precio,
            moneda=moneda,
            fecha_relevamiento=dto.fecha_relevamiento,
            servicio_raw=dto.servicio_raw,
            modalidad=modalidad,
            precio_raw=precio_raw if precio_raw is not None else dto.precio_raw,
        )

    crear_oferta_desde_dto = crear_desde_dto
