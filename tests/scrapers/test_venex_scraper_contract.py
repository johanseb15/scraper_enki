from src.infraestructura.scrapers.venex import VenexScraper
from src.aplicacion.dto.oferta_dto import OfertaDTO


class FakeDownloader:

    def descargar(self, url):
        return "<html>contenido venex</html>"


class FakeParser:

    def parsear(self, html_content, url_fuente):
        return [
            OfertaDTO(
                empresa_nombre="Venex",
                provincia="Córdoba",
                ciudad="Córdoba",
                fuente=url_fuente,
                servicio_raw="Notebook Lenovo",
                precio_raw="$ 850.000",
            )
        ]


def test_venex_scraper_debe_orquestar_downloader_y_parser():

    scraper = VenexScraper(
        downloader=FakeDownloader(),
        parser=FakeParser(),
    )

    resultado = scraper.obtener_servicios()

    assert isinstance(resultado, list)
    assert len(resultado) == 1

    oferta = resultado[0]

    assert isinstance(oferta, OfertaDTO)
    assert oferta.empresa_nombre == "Venex"
    assert oferta.servicio_raw == "Notebook Lenovo"
    assert oferta.precio_raw == "$ 850.000"

def test_venex_scraper_no_debe_entregar_ofertas_incompletas():

    scraper = VenexScraper(
        downloader=FakeDownloader(),
        parser=FakeParser(),
    )

    resultado = scraper.obtener_servicios()

    for oferta in resultado:
        assert oferta.empresa_nombre
        assert oferta.fuente
        assert oferta.servicio_raw
        assert oferta.precio_raw    