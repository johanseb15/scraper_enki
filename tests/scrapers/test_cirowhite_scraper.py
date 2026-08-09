from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.cirowhite import CiroWhiteScraper


class DownloaderFalso:
    def __init__(self, html: str):
        self.html = html
        self.urls: list[str] = []

    def descargar(self, url: str) -> str:
        self.urls.append(url)
        return self.html


def test_scraper_cirowhite_usa_downloader_y_expone_rechazos_trazables():
    html = """
      <div id="tab-imp" class="tab-content">
        <div class="pc">
          <div class="pc-name">Diagnóstico</div>
          <div class="pc-price">$5.000</div>
          <div class="pc-note">Se bonifica con la reparación</div>
          <ul class="pc-feats"><li>Evaluación completa</li></ul>
        </div>
        <div class="pc">
          <div class="pc-name">Mantenimiento Preventivo</div>
          <div class="pc-price">Desde $45.000</div>
        </div>
      </div>
      <footer><div class="ft-brand-name">CiroWhite Informática</div>
      <p>San Miguel de Tucumán, Tucumán</p></footer>
    """
    downloader = DownloaderFalso(html)
    scraper = CiroWhiteScraper(downloader=downloader)

    resultado = scraper.obtener_servicios()

    assert isinstance(scraper, BaseScraper)
    assert downloader.urls == [CiroWhiteScraper.URL]
    assert len(resultado) == 1
    assert isinstance(resultado[0], OfertaDTO)
    assert resultado[0].servicio_raw == "Diagnóstico"
    assert resultado[0].precio_raw == "$5.000"
    assert scraper.fuente == "CiroWhite Informática"
    assert len(scraper.rechazos) == 1
    assert scraper.rechazos[0].fuente == CiroWhiteScraper.URL
