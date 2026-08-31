from datetime import date

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.metricas import MetricasEjecucion
from src.pipeline import PipelineOfertas
from src.infraestructura.scrapers.base import BaseScraper


class RepositorioEnMemoria:
    def __init__(self):
        self.guardadas = []

    def guardar(self, oferta):
        self.guardadas.append(oferta)


class ScraperExitoso(BaseScraper):
    fuente = "Fuente exitosa"

    def obtener_servicios(self) -> list[OfertaDTO]:
        return [
            OfertaDTO(
                empresa_nombre="Vida Informatica",
                provincia="Córdoba",
                ciudad="Córdoba",
                servicio_raw="Eliminación de malware",
                precio=15000,
                moneda="ARS",
                fuente=self.fuente,
                fecha_relevamiento=date(2026, 8, 8),
            )
        ]


class ScraperFallido(BaseScraper):
    fuente = "Fuente fallida"

    def obtener_servicios(self) -> list[OfertaDTO]:
        raise RuntimeError("fallo durante la descarga")


def test_pipeline_expone_metricas_de_exito_y_fallo_sin_interrumpirse():
    repositorio = RepositorioEnMemoria()
    pipeline = PipelineOfertas(
        scrapers=[ScraperFallido(), ScraperExitoso()],
        repositorio=repositorio,
    )

    ofertas = pipeline.ejecutar()

    assert len(ofertas) == 1
    assert len(repositorio.guardadas) == 1
    assert isinstance(pipeline.metricas, MetricasEjecucion)
    assert pipeline.metricas.exitosos == ["ScraperExitoso"]
    assert pipeline.metricas.fallidos == ["ScraperFallido"]
    assert pipeline.metricas.total == 2
