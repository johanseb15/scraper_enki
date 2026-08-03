from pathlib import Path
from unittest.mock import patch

from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.scrapers.vida_informatica import VidaInformaticaScraper
from src.dominio.servicios import ServicioCanonico


def test_pipeline_scraper_html_a_persistencia(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "vida_informatica.html"
    html = fixture.read_text(encoding="utf-8")

    with patch("src.scrapers.vida_informatica.descargar_html", return_value=html):
        scraper = VidaInformaticaScraper()
        dtos = scraper.obtener_servicios()

    repositorio = RepositorioSQLiteOfertas(ruta_db=str(tmp_path / "vida_informatica.db"))
    procesador = ProcesadorOfertas(repositorio=repositorio)

    ofertas = [procesador.procesar(dto) for dto in dtos]

    assert len(dtos) > 0
    assert all(oferta is not None for oferta in ofertas)

    oferta = ofertas[0]
    assert oferta.empresa.nombre == "Vida Informatica"
    assert oferta.servicio == ServicioCanonico.MALWARE
    assert oferta.precio.valor == 15000
    assert oferta.precio.moneda == "ARS"
    assert oferta.empresa.provincia == "Córdoba"
    assert oferta.empresa.ciudad == "Córdoba"

    persistidas = repositorio.obtener_todas()
    assert len(persistidas) == 1
    assert persistidas[0].servicio == ServicioCanonico.MALWARE
