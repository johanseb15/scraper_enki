import pytest
from src.scrapers.venex_parser import VenexParser
from src.aplicacion.dto.oferta_dto import OfertaDTO


@pytest.fixture
def html_venex_muestra():
    return """
    <div class="product-box">
        <h3 class="product-title">NVIDIA GEFORCE RTX 4060 8GB GDDR6</h3>
        <div class="prices">
            <span class="product-box-old-price pull-right">$ 650.000</span>
            <span class="current-price">$ 589.999</span>
        </div>
    </div>
    <div class="product-box">
        <h3 class="product-title">MEMORIA KINGSTON FURY 16GB DDR5 5600MHZ</h3>
        <div class="prices">
            <span class="current-price">$ 85.500,00</span>
        </div>
    </div>
    """


class TestVenexParser:

    def test_parsea_html_de_venex_y_retorna_lista_de_oferta_dto(self, html_venex_muestra):
        # Arrange
        url_fuente = "https://www.venex.com.ar/componentes-de-pc"
        parser = VenexParser()

        # Act
        resultado = parser.parsear(html_content=html_venex_muestra, url_fuente=url_fuente)

        # Assert
        assert len(resultado) == 2
        assert isinstance(resultado[0], OfertaDTO)
        assert resultado[0].empresa_nombre == "Venex"
        assert resultado[0].servicio_raw == "NVIDIA GEFORCE RTX 4060 8GB GDDR6"
        assert resultado[0].precio_raw == "$ 589.999"
        assert resultado[0].fuente == url_fuente