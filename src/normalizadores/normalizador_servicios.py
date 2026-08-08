from src.dominio.catalogos.servicios import CatalogoServicios
from src.dominio.servicios import DetalleServicioCanonico, ServicioCanonico


class NormalizadorServicios:
    def __init__(self, catalogo: CatalogoServicios | None = None):
        self.catalogo = catalogo or CatalogoServicios()

    def normalizar(self, texto: str) -> ServicioCanonico:
        servicio = self.catalogo.resolver_desde_raw(texto)
        return servicio.id if servicio else ServicioCanonico.DESCONOCIDO

    def normalizar_avanzado(self, texto: str) -> DetalleServicioCanonico:
        servicio = self.catalogo.resolver_desde_raw(texto)

        if servicio:
            return DetalleServicioCanonico(
                categoria="soporte_tecnico",
                subcategoria=servicio.id.value,
                nombre_normalizado=servicio.nombre_display,
                confianza=0.95,
            )

        return DetalleServicioCanonico(
            categoria="desconocido",
            subcategoria="desconocido",
            nombre_normalizado=texto,
            confianza=0.0,
        )
