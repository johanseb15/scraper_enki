import logging
from typing import List, Optional

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.oferta_factory import OfertaFactory
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.aplicacion.puertos.repositorio_ofertas import RepositorioOfertas
from src.dominio.oferta import Oferta
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.scrapers.baires_cloud import BairesCloudScraper
from src.scrapers.base import BaseScraper
from src.scrapers.vida_informatica import VidaInformaticaScraper

logger = logging.getLogger(__name__)


class PipelineOfertas:
    """Orquestador principal del pipeline ETL de Enki."""

    @staticmethod
    def _identificar_fuente(scraper: BaseScraper) -> str:
        return (
            getattr(scraper, "fuente", None)
            or getattr(scraper, "URL", None)
            or getattr(scraper, "url_base", None)
            or scraper.__class__.__name__
        )

    def __init__(
        self,
        scrapers: Optional[List[BaseScraper]] = None,
        repositorio: Optional[RepositorioOfertas] = None,
        procesador: Optional[ProcesadorOfertas] = None,
    ):
        self.scrapers = scrapers or [
            BairesCloudScraper(),
            VidaInformaticaScraper(),
        ]
        self.repositorio = repositorio or RepositorioSQLiteOfertas()
        self.procesador = procesador or ProcesadorOfertas(
            factory=OfertaFactory(),
            repositorio=self.repositorio,
        )

    def ejecutar(self) -> List[Oferta]:
        dtos_totales: List[OfertaDTO] = []

        # 1. Extracción (Scraping -> DTOs)
        for scraper in self.scrapers:
            nombre_scraper = scraper.__class__.__name__
            fuente = self._identificar_fuente(scraper)
            try:
                logger.info(f"Ejecutando scraper: {nombre_scraper}")
                dtos = scraper.obtener_servicios()
                dtos_totales.extend(dtos)
                logger.info(f"{nombre_scraper} extrajo {len(dtos)} DTOs.")
            except Exception as e:
                logger.error(
                    f"Error al ejecutar fuente {fuente} ({nombre_scraper}): {e}",
                    exc_info=True,
                )

        # 2. Transformación, Normalización y Persistencia
        logger.info(
            f"Procesando y guardando {len(dtos_totales)} DTOs en total..."
        )
        ofertas_guardadas = self.procesador.ejecutar(dtos_totales)

        logger.info(
            f"Pipeline finalizado. Se guardaron {len(ofertas_guardadas)} ofertas con éxito."
        )
        return ofertas_guardadas


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    pipeline = PipelineOfertas()
    ofertas = pipeline.ejecutar()
    print(f"\n[OK] Pipeline finalizado. Total de ofertas procesadas y guardadas: {len(ofertas)}")
