from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.scrapers.vida_informatica_scraper import VidaInformaticaScraper
from src.infraestructura.scrapers.baires_cloud import BairesCloudScraper
from src.infraestructura.scrapers.venex_scraper import VenexScraper
from src.dominio.oferta import Oferta

class FakeDownloader:

    def descargar(self, url):
        return "<html></html>"


def obtener_scrapers():

    return [
        VenexScraper(
            downloader=FakeDownloader(),
        ),
        VidaInformaticaScraper(
            downloader=FakeDownloader(),
        ),
        BairesCloudScraper(),
    ]


def test_todos_los_scrapers_deben_devolver_lista_de_oferta_dto():

    for scraper in obtener_scrapers():

        resultado = scraper.obtener_servicios()

        assert isinstance(resultado, list)

        for oferta in resultado:
            assert isinstance(oferta, OfertaDTO)


def test_todas_las_ofertas_deben_tener_origen_y_datos_minimos():

    for scraper in obtener_scrapers():

        resultado = scraper.obtener_servicios()

        for oferta in resultado:
            assert oferta.fuente
            assert oferta.empresa_nombre
            assert oferta.servicio_raw


def test_scrapers_no_deben_devolver_entidades_de_dominio():

    for scraper in obtener_scrapers():

        resultado = scraper.obtener_servicios()

        for oferta in resultado:
            assert not isinstance(oferta, Oferta)
