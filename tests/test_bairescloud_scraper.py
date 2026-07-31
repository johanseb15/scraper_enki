from unittest.mock import patch
from src.scrapers.baires_cloud import BairesCloudScraper


def test_bairescloud_scraper_descarga_y_extrae_servicios():
    html = """
    <html>
        <body>
            <table>
                <thead>
                    <tr><th>Servicio</th><th>Equipo</th><th>Precio</th></tr>
                </thead>
                <tbody>
                    <tr><td>Soporte remoto</td><td>PC</td><td>$25.000,00</td></tr>
                    <tr><td>Visita técnica</td><td>PC</td><td>$40.000,00</td></tr>
                </tbody>
            </table>
        </body>
    </html>
    """
    scraper = BairesCloudScraper()

    with patch(
        "src.scrapers.baires_cloud.descargar_html", return_value=html
    ):
        resultados = scraper.obtener_servicios()

    assert len(resultados) == 2
    # Corrección: El scraper concatena el servicio con la columna de equipo
    assert resultados[0].servicio_raw == "Soporte remoto - PC"
