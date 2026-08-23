"""Entry point para la ingesta masiva de ofertas de CompraGamer."""

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import logging
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.infraestructura.scrapers.compragamer_scraper import CompraGamerScraper
from src.configuracion_runtime import resolver_ruta_db_ofertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.pipeline import PipelineOfertas
from src.infraestructura.scrapers.base import BaseScraper


logger = logging.getLogger(__name__)


def ejecutar_ingesta(
    db_path: str | None = None,
    scrapers: Sequence[BaseScraper] | None = None,
) -> int:
    """Ejecuta el pipeline oficial y devuelve la cantidad de ofertas guardadas."""
    scrapers_seleccionados = (
        list(scrapers) if scrapers is not None else [CompraGamerScraper()]
    )
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=resolver_ruta_db_ofertas(db_path)
    )
    pipeline = PipelineOfertas(
        scrapers=scrapers_seleccionados,
        repositorio=repositorio,
    )

    ofertas = pipeline.ejecutar()
    logger.info("Ingesta completada. Total persistido: %d ofertas.", len(ofertas))
    return len(ofertas)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ejecutar_ingesta()
