from datetime import date
from unittest.mock import MagicMock, patch

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.scrapers.compragamer_playwright_scraper import (
    CompraGamerPlaywrightScraper as CompraGamerPlaywrightScraperOficial,
)
from src.scrapers.compragamer_parser import parsear_ofertas_compragamer
from src.scrapers.compragamer_playwright_scraper import (
    CompraGamerPlaywrightScraper as CompraGamerPlaywrightScraperLegacy,
)


def test_ruta_legacy_reexporta_scraper_oficial():
    assert CompraGamerPlaywrightScraperLegacy is CompraGamerPlaywrightScraperOficial


def test_parsear_ofertas_compragamer_exito():
    mock_data = [
        {
            "id_producto": 100,
            "nombre": "AMD Ryzen 5 5600X",
            "precioEspecial": "215000.00",
            "precioLista": 250000,
        },
        {
            "id_producto": 101,
            "nombre": "Nvidia RTX 4060 8GB",
            "precioEspecial": 450000,
        },
        {
            "id_producto": 102,
            "nombre": "Producto Invalido",
            "precioEspecial": 0,
        },
    ]

    fecha = date(2026, 8, 4)
    ofertas = parsear_ofertas_compragamer(mock_data, fecha)

    assert len(ofertas) == 2
    assert isinstance(ofertas[0], OfertaDTO)
    assert ofertas[0].empresa_nombre == "Compra Gamer"
    assert ofertas[0].servicio_raw == "AMD Ryzen 5 5600X"
    assert ofertas[0].precio == 215000
    assert ofertas[0].precio_raw == "215000.00"
    assert ofertas[0].moneda == "ARS"
    assert ofertas[0].fuente == "compragamer_playwright"


@patch(
    "src.infraestructura.scrapers.compragamer_playwright_scraper.sync_playwright"
)
def test_compragamer_playwright_scraper_obtener_ofertas(mock_playwright):
    # Mocking de la cadena de objetos de Playwright
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    
    mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    # Simulamos el callback de respuesta de la API
    def fake_goto(url, **kwargs):
        callback = None
        for call in mock_page.on.call_args_list:
            if call[0][0] == "response":
                callback = call[0][1]
                break
        
        if callback:
            fake_response = MagicMock()
            fake_response.status = 200
            fake_response.url = "https://static.compragamer.com/productos"
            fake_response.json.return_value = [
                {
                    "id_producto": 1,
                    "nombre": "Placa de Video RX 6600",
                    "precioEspecial": 300000,
                }
            ]
            callback(fake_response)

    mock_page.goto.side_effect = fake_goto

    scraper = CompraGamerPlaywrightScraperLegacy()
    resultado = scraper.obtener_ofertas(date(2026, 8, 4))

    assert len(resultado) == 1
    assert resultado[0].servicio_raw == "Placa de Video RX 6600"
    assert resultado[0].precio == 300000
