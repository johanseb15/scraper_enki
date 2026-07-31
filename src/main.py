import logging
from typing import Sequence
from src.scrapers.base import BaseScraper
from src.scrapers.vida_informatica import VidaInformaticaScraper
from src.scrapers.baires_cloud import BairesCloudScraper
from src.repositorio import RepositorioSQLite
from src.reporte import generar_resumen_servicio
from src.presentacion import generar_reporte_texto
from src.metricas import MetricasEjecucion, ResultadoEjecucion
from src.normalizacion import es_mismo_servicio


logger = logging.getLogger(__name__)


def ejecutar(
    ruta_db: str = "enki.db",
    scrapers: Sequence[BaseScraper] | None = None,
    servicio_target: str = "Eliminación de malware"
) -> ResultadoEjecucion:
    """Orquesta la extracción, persistencia y generación de reporte.
    
    Registra métricas de ejecución y tolera fallos individuales por scraper.
    """
    if scrapers is None:
        scrapers = [
            VidaInformaticaScraper(),
            BairesCloudScraper(),
        ]

    repo = RepositorioSQLite(ruta_db)
    metricas = MetricasEjecucion()

    for scraper in scrapers:
        nombre_scraper = scraper.__class__.__name__
        try:
            servicios = scraper.obtener_servicios()
            for servicio in servicios:
                repo.guardar(servicio)
            metricas.registrar_exito(nombre_scraper)
        except Exception as error:
            metricas.registrar_fallo(nombre_scraper)
            logger.error(
                "Falló la ejecución del scraper %s: %s", 
                nombre_scraper, 
                error
            )

    datos = repo.obtener_todos()
    
    if datos and not any(es_mismo_servicio(s.servicio, servicio_target) for s in datos):
        servicio_target = datos[0].servicio

    resumen = generar_resumen_servicio(datos, servicio_target)
    reporte = generar_reporte_texto(resumen)

    print(reporte)
    print(metricas.resumen_texto())

    return ResultadoEjecucion(reporte=reporte, metricas=metricas)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ejecutar()
