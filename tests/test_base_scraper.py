import pytest

from src.infraestructura.scrapers.base import BaseScraper as BaseScraperOficial
from src.infraestructura.scrapers.vida_informatica import (
    VidaInformaticaScraper as VidaInformaticaScraperOficial,
)
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.vida_informatica import VidaInformaticaScraper
from src.infraestructura.scrapers.baires_cloud import BairesCloudScraper


def test_base_scraper_es_clase_abstracta():
    assert BaseScraper is BaseScraperOficial

    with pytest.raises(TypeError):
        BaseScraper()


def test_scrapers_implementan_interfaz_base():
    assert VidaInformaticaScraper is VidaInformaticaScraperOficial
    assert issubclass(VidaInformaticaScraper, BaseScraper)
    assert issubclass(BairesCloudScraper, BaseScraper)


def test_scrapers_implementan_obtener_servicios():
    assert "obtener_servicios" in VidaInformaticaScraper.__dict__ or hasattr(VidaInformaticaScraper, "obtener_servicios")
    assert "obtener_servicios" in BairesCloudScraper.__dict__ or hasattr(BairesCloudScraper, "obtener_servicios")
