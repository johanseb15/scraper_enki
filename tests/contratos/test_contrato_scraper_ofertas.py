from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.dominio.oferta import Oferta
from src.infraestructura.scrapers.baires_cloud import BairesCloudScraper
from src.infraestructura.scrapers.venex import VenexScraper
from src.infraestructura.scrapers.vida_informatica import VidaInformaticaScraper


class FakeDownloader:
    def __init__(self, html):
        self.html = html

    def descargar(self, url):
        return self.html


def obtener_scrapers():
    html_venex = """
        <div class="product-box">
            <h3 class="product-box-title">Notebook Lenovo</h3>
            <span class="current-price">$ 850.000</span>
        </div>
    """
    html_vida = """
        <table>
            <tr>
                <th>Servicio</th><th>Equipo</th>
                <th>Freelance</th><th>Local</th>
            </tr>
            <tr>
                <td>Eliminación de malware</td><td>PC</td>
                <td>$ 15.000</td><td>$ 20.000</td>
            </tr>
        </table>
    """
    html_baires = """
        <table>
            <thead>
                <tr><th>Servicio</th><th>Equipo</th><th>Precio</th></tr>
            </thead>
            <tbody>
                <tr><td>Soporte remoto</td><td>PC</td><td>$25.000,00</td></tr>
            </tbody>
        </table>
    """
    return [
        VenexScraper(downloader=FakeDownloader(html_venex)),
        VidaInformaticaScraper(downloader=FakeDownloader(html_vida)),
        BairesCloudScraper(downloader=FakeDownloader(html_baires)),
    ]


def test_todos_los_scrapers_deben_devolver_lista_de_oferta_dto():
    for scraper in obtener_scrapers():
        resultado = scraper.obtener_servicios()

        assert resultado
        assert isinstance(resultado, list)
        assert all(isinstance(oferta, OfertaDTO) for oferta in resultado)


def test_todas_las_ofertas_deben_tener_origen_y_datos_minimos():
    for scraper in obtener_scrapers():
        resultado = scraper.obtener_servicios()

        assert resultado
        for oferta in resultado:
            assert oferta.fuente
            assert oferta.empresa_nombre
            assert oferta.servicio_raw


def test_scrapers_no_deben_devolver_entidades_de_dominio():
    for scraper in obtener_scrapers():
        resultado = scraper.obtener_servicios()

        assert resultado
        assert all(not isinstance(oferta, Oferta) for oferta in resultado)
