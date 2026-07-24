import logging
from typing import Sequence
from src.scrapers.base import BaseScraper
from src.scrapers.vida_informatica import VidaInformaticaScraper
from src.scrapers.baires_cloud import BairesCloudScraper
from src.repositorio import RepositorioSQLite
from src.reporte import generar_resumen_servicio
from src.presentacion import generar_reporte_texto

logger = logging.getLogger(__name__)


def ejecutar(
    ruta_db: str = "enki.db",
    scrapers: Sequence[BaseScraper] | None = None,
    servicio_target: str = "Eliminación de malware"
) -> str:
    """Orquesta la extracción, persistencia y generación de reporte.
    
    Captura excepciones individuales por scraper para mantener el pipeline resiliente.
    """
    if scrapers is None:
        scrapers = [
            VidaInformaticaScraper(),
            BairesCloudScraper(),
        ]

    repo = RepositorioSQLite(ruta_db)

    for scraper in scrapers:
        try:
            servicios = scraper.obtener_servicios()
            for servicio in servicios:  # Corrección: 'in' en vez de 'en'
                repo.guardar(servicio)
        except Exception as error:
            logger.error(
                "Falló la ejecución del scraper %s: %s", 
                scraper.__class__.__name__, 
                error
            )

    datos = repo.obtener_todos()
    
    if datos and not any(s.servicio.lower() == servicio_target.lower() for s in datos):
        servicio_target = datos[0].servicio

    resumen = generar_resumen_servicio(datos, servicio_target)
    reporte = generar_reporte_texto(resumen)

    print(reporte)
    return reporte


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ejecutar()