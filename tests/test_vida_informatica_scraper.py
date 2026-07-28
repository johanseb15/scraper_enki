from pathlib import Path
from unittest.mock import patch

from src.scrapers.vida_informatica import VidaInformaticaScraper
from src.modelos.servicio_precio import ServicioPrecio


def test_vida_informatica_scraper_orquesta_descarga_y_parseo():

    ruta_html = (
        Path(__file__).parent
        / "fixtures"
        / "vida_informatica_zona1.html"
    )

    html_mockeo = ruta_html.read_text(
        encoding="utf-8"
    )

    with patch(
        "src.scrapers.vida_informatica.descargar_html"
    ) as mock_descargar_html:

        mock_descargar_html.return_value = html_mockeo

        scraper = VidaInformaticaScraper()

        resultados = scraper.obtener_servicios()

        assert isinstance(resultados, list)

        assert len(resultados) > 0

        assert isinstance(
            resultados[0],
            ServicioPrecio
        )

        mock_descargar_html.assert_called_once_with(
            "https://vidainformatica.com.ar/listado-de-precios-zona-1/"
        )


def test_vida_informatica_asigna_ciudad():

    ruta_html = (
        Path(__file__).parent
        / "fixtures"
        / "vida_informatica_zona1.html"
    )

    html_mockeo = ruta_html.read_text(
        encoding="utf-8"
    )

    with patch(
        "src.scrapers.vida_informatica.descargar_html"
    ) as mock_descargar_html:

        mock_descargar_html.return_value = html_mockeo

        scraper = VidaInformaticaScraper()

        servicios = scraper.obtener_servicios()

    assert len(servicios) > 0

    assert servicios[0].ciudad == "Córdoba"