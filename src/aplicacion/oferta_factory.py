from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.dominio.modelos.oferta import Oferta
from src.normalizadores.normalizador_servicios import NormalizadorServicios


class OfertaFactory:

    def __init__(self, normalizador: NormalizadorServicios | None = None):
        self.normalizador = normalizador or NormalizadorServicios()

    def crear_desde_dto(self, dto: OfertaDTO) -> Oferta:
        servicio_canonico = self.normalizador.normalizar(dto.servicio_raw)

        # Mapeo flexible de atributos para soportar distintas versiones del DTO
        empresa = getattr(dto, "empresa_nombre", getattr(dto, "empresa", None))
        fuente = getattr(dto, "fuente", getattr(dto, "url", None))
        precio_final = dto.precio if dto.precio is not None else dto.precio_raw

        return Oferta(
            titulo=dto.servicio_raw,
            precio=precio_final,
            moneda=dto.moneda,
            servicio=servicio_canonico,
            proveedor=empresa,
            url=fuente,
        )