from unittest.mock import Mock

from src.scrapers.vida_informatica import VidaInformaticaScraper


def test_scraper_utiliza_un_downloader_inyectado():
    downloader = Mock()
    downloader.descargar.return_value = (
        "<html><table><tr>"
        "<td>Eliminación de malware</td>"
        "<td>$29.816</td>"
        "<td>$41.411</td>"
        "</tr></table></html>"
    )

    scraper = VidaInformaticaScraper(downloader=downloader)

    scraper.obtener_servicios()

    downloader.descargar.assert_called_once()
