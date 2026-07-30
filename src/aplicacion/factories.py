from datetime import date
from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico
from src.aplicacion.dtos import OfertaDTO


class OfertaFactory:

    def crear(self, dto: OfertaDTO, servicio_canonico: ServicioCanonico, fecha_relevamiento: date) -> Oferta:
        empresa = Empresa(
            nombre=dto.empresa,
            provincia=dto.provincia,
            ciudad=dto.ciudad,
            fuente=dto.fuente
        )

        return Oferta(
            empresa=empresa,
            servicio=servicio_canonico,
            precio=dto.precio,
            moneda=dto.moneda,
            fecha_relevamiento=fecha_relevamiento
        )