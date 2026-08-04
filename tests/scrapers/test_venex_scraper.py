from src.scrapers.venex import VenexScraper
from src.aplicacion.dto.oferta_dto import OfertaDTO


class FakeDownloader:

    def descargar(self, url):
        return """
        <div class="product-box">
            <h3 class="product-box-title">
                <a>Notebook Lenovo Thinkpad</a>
            </h3>

            <span class="current-price">
                $ 850.000
            </span>
        </div>
        """


def test_venex_scraper_obtiene_ofertas_desde_downloader():

    scraper = VenexScraper(
        downloader=FakeDownloader()
    )

    resultado = scraper.obtener_servicios()

    assert len(resultado) == 1

    oferta = resultado[0]

    assert isinstance(oferta, OfertaDTO)
    assert oferta.empresa_nombre == "Venex"
    assert oferta.servicio_raw == "Notebook Lenovo Thinkpad"
    assert oferta.precio_raw == "$ 850.000"