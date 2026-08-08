import logging
from typing import Sequence

from src.aplicacion.oferta_factory import OfertaFactory
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.metricas import ResultadoEjecucion
from src.pipeline import PipelineOfertas
from src.presentacion import generar_reporte_texto
from src.reporte import generar_resumen_servicio
from src.scrapers.baires_cloud import BairesCloudScraper
from src.scrapers.base import BaseScraper
from src.scrapers.vida_informatica import VidaInformaticaScraper


def ejecutar(
    ruta_db: str = "enki.db",
    scrapers: Sequence[BaseScraper] | None = None,
    servicio_target: str = "Eliminación de malware",
) -> ResultadoEjecucion:
    """Construye y ejecuta el pipeline oficial y genera su reporte."""
    scrapers_seleccionados = list(scrapers) if scrapers is not None else [
        VidaInformaticaScraper(),
        BairesCloudScraper(),
    ]

    repositorio = RepositorioSQLiteOfertas(ruta_db=ruta_db)
    procesador = ProcesadorOfertas(
        factory=OfertaFactory(),
        repositorio=repositorio,
    )
    pipeline = PipelineOfertas(
        scrapers=scrapers_seleccionados,
        repositorio=repositorio,
        procesador=procesador,
    )

    ofertas = pipeline.ejecutar()
    resumen = generar_resumen_servicio(ofertas, servicio_target)
    reporte = generar_reporte_texto(resumen)

    print(reporte)
    print(pipeline.metricas.resumen_texto())

    return ResultadoEjecucion(reporte=reporte, metricas=pipeline.metricas)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ejecutar()
