"""Pipeline de ingesta masiva para el proyecto scraper_enki."""

import logging
import sys
from pathlib import Path

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Garantizar que el directorio raíz del proyecto esté en el PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.scrapers.compragamer_scraper import CompraGamerScraper
from src.dominio.normalizador import NormalizadorCategorias
from src.dominio.dtos import OfertaDTO


def _convertir_a_dto(item) -> OfertaDTO:
    """Convierte una oferta extraída (dict u objeto) a OfertaDTO."""
    if isinstance(item, OfertaDTO):
        return item
    if isinstance(item, dict):
        return OfertaDTO(
            nombre=item.get("nombre") or item.get("titulo") or item.get("titulo_raw", "Oferta"),
            titulo_raw=item.get("titulo_raw") or item.get("nombre") or item.get("titulo", "Oferta"),
            precio=float(item.get("precio", 0.0)),
            moneda=item.get("moneda", "ARS"),
            url=item.get("url", ""),
            proveedor=item.get("proveedor", "CompraGamer"),
            categoria_normalizada=item.get("categoria_normalizada", "General"),
            subcategoria_normalizada=item.get("subcategoria_normalizada", "otros"),
        )
    return item


def ejecutar_ingesta(db_path: str = "enki.db"):
    """Ejecuta el pipeline completo: extracción, normalización y persistencia."""
    logger.info("Iniciando pipeline de ingesta masiva en %s...", db_path)

    repo = RepositorioSQLiteOfertas(db_path=db_path)
    normalizador = NormalizadorCategorias()
    total_guardadas = 0

    # 1. Extracción de ofertas
    try:
        scraper = ScraperCompraGamer()
        ofertas_raw = scraper.obtener_ofertas()
        logger.info("CompraGamer: %d ofertas extraídas.", len(ofertas_raw))
    except Exception as e:
        logger.error("Error durante la extracción de datos: %s", e, exc_info=True)
        return

    # 2. Normalización y Persistencia
    try:
        for item in ofertas_raw:
            dto = _convertir_a_dto(item)
            resultado_norm = normalizador.normalizar(dto)

            # Manejo si la normalización retorna una tupla (categoria, subcategoria)
            if isinstance(resultado_norm, (tuple, list)):
                cat = str(resultado_norm[0]) if len(resultado_norm) > 0 else "General"
                subcat = str(resultado_norm[1]) if len(resultado_norm) > 1 else "otros"
                dto.categoria_normalizada = cat
                dto.subcategoria_normalizada = subcat
                dto_normalizado = dto
            elif hasattr(resultado_norm, "categoria_normalizada"):
                dto_normalizado = resultado_norm
            else:
                dto_normalizado = dto

            # Sanitización defensiva de tipos de datos antes de la inserción
            cat = getattr(dto_normalizado, "categoria_normalizada", "General")
            subcat = getattr(dto_normalizado, "subcategoria_normalizada", "otros")

            if not isinstance(cat, str):
                cat = str(cat)
            if not isinstance(subcat, str) or str(subcat).lower().startswith("ofertadto"):
                subcat = "otros"

            dto_normalizado.categoria_normalizada = cat
            dto_normalizado.subcategoria_normalizada = subcat

            # Persistencia en SQLite
            repo.guardar(dto_normalizado)
            total_guardadas += 1

        logger.info("Ingesta completada. Total persistido: %d ofertas.", total_guardadas)

    except Exception as e:
        logger.error("Error durante el proceso de ingesta: %s", e, exc_info=True)
        logger.info("Ingesta completada. Total persistido: %d ofertas.", total_guardadas)


if __name__ == "__main__":
    ejecutar_ingesta()