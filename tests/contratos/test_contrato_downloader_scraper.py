from src.infraestructura.scrapers.vida_informatica import VidaInformaticaScraper
from src.infraestructura.scrapers.venex import VenexScraper
from src.infraestructura.scrapers.baires_cloud import BairesCloudScraper


class FakeDownloader:

    def descargar(self, url):
        return "<html></html>"


def test_scrapers_deben_aceptar_downloader_inyectado():

    scrapers = [
        VenexScraper(
            downloader=FakeDownloader()
        ),
        VidaInformaticaScraper(
            downloader=FakeDownloader()
        ),
        BairesCloudScraper(
            downloader=FakeDownloader()
        ),
    ]

    assert len(scrapers) == 3