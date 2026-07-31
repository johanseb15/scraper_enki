import pytest

from src.scrapers.base import BaseScraper
from src.scrapers.vida_informatica import VidaInformaticaScraper
from src.scrapers.baires_cloud import BairesCloudScraper


def test_base_scraper_es_clase_abstracta():
    with pytest.raises(TypeError):
        BaseScraper()


def test_scrapers_implementan_interfaz_base():
    assert issubclass(VidaInformaticaScraper, BaseScraper)
    assert issubclass(BairesCloudScraper, BaseScraper)


def test_scrapers_implementan_obtener_servicios():
    assert "obtener_servicios" in VidaInformaticaScraper.__dict__ or hasattr(VidaInformaticaScraper, "obtener_servicios")
    assert "obtener_servicios" in BairesCloudScraper.__dict__ or hasattr(BairesCloudScraper, "obtener_servicios")
