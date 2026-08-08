from pathlib import Path

from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.scrapers.vida_informatica import VidaInformaticaScraper


class FakeDownloader:
    def __init__(self, html):
        self.html = html

    def descargar(self, url):
        return self.html


def test_pipeline_multi_oferta_html_a_persistencia(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "vida_informatica.html"
    html = fixture.read_text(encoding="utf-8")

    scraper = VidaInformaticaScraper(downloader=FakeDownloader(html))
    dtos = scraper.obtener_servicios()

    repositorio = RepositorioSQLiteOfertas(ruta_db=str(tmp_path / "multi_oferta.db"))
    procesador = ProcesadorOfertas(repositorio=repositorio)

    ofertas = [procesador.procesar(dto) for dto in dtos]

    assert len(dtos) == 3
    assert all(dto.servicio_raw for dto in dtos)
    assert all(oferta is not None for oferta in ofertas)

    servicios_esperados = {
        ServicioCanonico.MALWARE,
        ServicioCanonico.MANTENIMIENTO,
        ServicioCanonico.SOPORTE_REDES,
    }
    assert {oferta.servicio for oferta in ofertas} == servicios_esperados

    assert all(oferta.empresa.nombre == "Vida Informatica" for oferta in ofertas)
    assert all(oferta.empresa.provincia == "Córdoba" for oferta in ofertas)
    assert all(oferta.empresa.ciudad == "Córdoba" for oferta in ofertas)
    assert all(oferta.precio.moneda == "ARS" for oferta in ofertas)

    persistidas = repositorio.obtener_todas()
    assert len(persistidas) == 3
    assert {oferta.servicio for oferta in persistidas} == servicios_esperados
