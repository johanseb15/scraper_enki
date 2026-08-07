from src.aplicacion.oferta_factory import OfertaFactory


class ProcesadorOfertas:
    def __init__(
        self,
        factory: OfertaFactory | None = None,
        repositorio=None,
        normalizador_ubicaciones=None,
        normalizador_empresas=None,
        normalizador_servicios=None,
    ):
        self.factory = factory or OfertaFactory()
        self.repositorio = repositorio

        self.normalizador_ubicaciones = normalizador_ubicaciones
        self.normalizador_empresas = normalizador_empresas
        self.normalizador_servicios = normalizador_servicios