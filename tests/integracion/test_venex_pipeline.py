import pytest
from src.scrapers.venex_parser import VenexParser
from src.normalizadores.normalizador_precios import NormalizadorPrecios


@pytest.fixture
def html_venex_muestra():
    return """
    <div class="product-box">
        <h3 class="product-title">NVIDIA GEFORCE RTX 4060 8GB GDDR6</h3>
        <div class="prices">
            <span class="current-price">$ 589.999</span>
        </div>
    </div>
    """


class TestVenexPipelineIntegration:

    def test_pipeline_transforma_dto_de_venex_a_datos_normalizados(self, html_venex_muestra):
        # Arrange
        parser = VenexParser()

        # Act
        dtos = parser.parsear(html_content=html_venex_muestra, url_fuente="https://www.venex.com.ar")
        dto = dtos[0]

        precio_objeto = NormalizadorPrecios.normalizar(dto.precio_raw)

        # Assert
        assert dto.empresa_nombre == "Venex"
        assert precio_objeto.valor == 589999
        assert precio_objeto.moneda == "ARS"
        assert dto.servicio_raw == "NVIDIA GEFORCE RTX 4060 8GB GDDR6"