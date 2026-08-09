from unittest.mock import Mock

from src.infraestructura.scrapers.dmr import DMRScraper


def test_dmr_scraper_usa_downloader_inyectado_y_expone_contexto():
    downloader = Mock()
    downloader.descargar.return_value = """
      <a class="nav-logo"><span>D</span>DMR Web Design</a>
      <div class="hero-badge">Mendoza Capital</div>
      <h2 class="section-title">Precios orientativos actualizados abril 2026</h2>
      <div class="service-card" data-cat="software">
        <div class="service-name">Eliminación de malware / virus</div>
        <span class="device-tag">PC</span>
        <div class="service-price">$29.000</div>
        <div class="service-price-label">Freelance / taller</div>
      </div>
    """

    scraper = DMRScraper(downloader=downloader)
    dtos = scraper.obtener_servicios()

    downloader.descargar.assert_called_once_with(DMRScraper.URL)
    assert len(dtos) == 1
    assert dtos[0].precio_raw == "$29.000"
    assert scraper.contexto.fecha_editorial_raw == "abril 2026"
    assert scraper.rechazos == []
