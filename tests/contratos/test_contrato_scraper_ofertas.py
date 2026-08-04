from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.scrapers.vida_informatica import VidaInformaticaScraper
from src.scrapers.baires_cloud import BairesCloudScraper
from src.scrapers.venex import VenexScraper
from src.dominio.oferta import Oferta

class FakeDownloader:

    def descargar(self, url):
        return "<html></html>"


class FakeParser:

    def parsear(self, html_content, url_fuente):
        return [
            OfertaDTO(
                empresa_nombre="Proveedor Test",
                fuente=url_fuente,
                servicio_raw="Servicio test",
                precio_raw="$ 1000",
            )
        ]


def obtener_scrapers():

    return [
        VenexScraper(
            downloader=FakeDownloader(),
            parser=FakeParser(),
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