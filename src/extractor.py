from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.scrapers.vida_informatica_parser import (
    extraer_datos_vida_informatica,
)


def extraer_datos(html: str) -> list[OfertaDTO]:
    return extraer_datos_vida_informatica(html)
