from src.aplicacion.dto.oferta_dto import OfertaDTO

def extraer_datos(html: str) -> list:
    try:
        from src.scrapers import extraer_datos as _extraer
        return _extraer(html)
    except ImportError:
        return []