from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.dominio.oferta import Oferta
from src.dominio.empresa import Empresa
from src.normalizadores.normalizador_empresas import NormalizadorEmpresas
from src.normalizadores.normalizador_servicios import NormalizadorServicios
from src.normalizadores.normalizador_precios import NormalizadorPrecios
from src.dominio.servicios import ServicioCanonico


class NormalizadorOfertas:

    def __init__(self):
        self.normalizador_empresas = NormalizadorEmpresas()
        self.normalizador_servicios = NormalizadorServicios()
        self.normalizador_precios = NormalizadorPrecios()

    def normalizar(self, dto: OfertaDTO) -> Oferta | None:

        servicio = self.normalizador_servicios.normalizar(
            dto.servicio_raw
        )

        if servicio is None or servicio == ServicioCanonico.DESCONOCIDO:
            return None

        precio = (
            self.normalizador_precios.normalizar(dto.precio_raw)
            if dto.precio_raw
            else dto.precio
        )

        if hasattr(precio, "valor"):
            precio = precio.valor

        empresa_nombre = self.normalizador_empresas.normalizar(
            dto.empresa_nombre
        )

        empresa = Empresa(
            nombre=empresa_nombre,
            provincia=dto.provincia,
            ciudad=dto.ciudad,
            fuente=dto.fuente,
        )

        return Oferta(
            empresa=empresa,
            servicio=servicio,
            precio=precio,
            moneda=dto.moneda or "ARS",
            fecha_relevamiento=dto.fecha_relevamiento,
        )