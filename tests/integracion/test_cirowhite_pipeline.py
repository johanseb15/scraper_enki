from src.infraestructura.scrapers.cirowhite import CiroWhiteScraper
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.pipeline import PipelineOfertas


class DownloaderFalso:
    def descargar(self, _url: str) -> str:
        return """
          <div id="tab-imp" class="tab-content">
            <div class="pc">
              <div class="pc-name">Diagnóstico</div>
              <div class="pc-price">$5.000</div>
            </div>
          </div>
          <div id="tab-pc" class="tab-content">
            <div class="pc">
              <div class="pc-name">Armado de PC</div>
              <div class="pc-price">$40.000–$70.000</div>
              <ul class="pc-feats"><li>Instalación componentes: $25.000</li></ul>
            </div>
          </div>
          <footer><div class="ft-brand-name">CiroWhite Informática</div>
          <p>San Miguel de Tucumán, Tucumán</p></footer>
        """


def test_cirowhite_atraviesa_pipeline_y_persiste_solo_precios_seguros(tmp_path):
    repositorio = RepositorioSQLiteOfertas(tmp_path / "cirowhite.db")
    scraper = CiroWhiteScraper(downloader=DownloaderFalso())
    pipeline = PipelineOfertas(scrapers=[scraper], repositorio=repositorio)

    ofertas = pipeline.ejecutar()
    persistidas = repositorio.obtener_todas()

    assert len(ofertas) == 2
    assert len(persistidas) == 2
    assert {(o.servicio_raw, o.precio.valor, o.precio_raw) for o in persistidas} == {
        ("Diagnóstico", 5000, "$5.000"),
        ("Instalación componentes", 25000, "$25.000"),
    }
    assert len(scraper.rechazos) == 1
    assert scraper.rechazos[0].razon == "Armado de PC: precio texto_especial '$40.000–$70.000'"
