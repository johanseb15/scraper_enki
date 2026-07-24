from pathlib import Path
from unittest.mock import patch
import pytest
from src.main import ejecutar
from src.extractor import extraer_datos

from datetime import date
from src.modelos.servicio_precio import ServicioPrecio
from src.repositorio import RepositorioSQLite
from src.scrapers.bairescloud import BairesCloudScraper

@pytest.fixture
def servicios_desde_fixture():
    """Carga el fixture local y lo parsea para simular la respuesta del scraper."""
    ruta_html = Path(__file__).parent / "fixtures" / "vida_informatica_zona1.html"
    html = ruta_html.read_text(encoding="utf-8")
    return extraer_datos(html)

def test_ejecutar_devuelve_un_reporte(tmp_path, servicios_desde_fixture):
    # Creamos una base de datos aislada para este test
    db_temporal = str(tmp_path / "test_enki.db")
    
    # Interceptamos el Scraper en main para que devuelva los datos del fixture
    with patch("src.main.VidaInformaticaScraper") as MockScraper:
        MockScraper.return_value.obtener_servicios.return_value = servicios_desde_fixture
        
        reporte = ejecutar(ruta_db=db_temporal)
        
        assert isinstance(reporte, str)
        assert len(reporte) > 0

def test_main_ejecuta_pipeline_completo(tmp_path, servicios_desde_fixture):
    db_temporal = str(tmp_path / "test_enki.db")
    
    with patch("src.main.VidaInformaticaScraper") as MockScraper:
        MockScraper.return_value.obtener_servicios.return_value = servicios_desde_fixture
        
        reporte = ejecutar(ruta_db=db_temporal)
        
        # Verificamos que el reporte contenga las secciones clave generadas por el flujo
        assert "Eliminación de malware" in reporte

def test_ejecutar_persiste_datos_de_ambos_scrapers(tmp_path):
    db_temporal = str(tmp_path / "test_enki.db")

    servicio_vida = ServicioPrecio(
        empresa="Vida informatica", provincia="", ciudad="",
        servicio="Eliminación de malware", equipo="PC",
        precio_freelance=29816, precio_local=41411, moneda="ARS",
        fecha_relevamiento=date(2026, 7, 20), fuente="",
    )
    servicio_baires = ServicioPrecio(
        empresa="BairesCloud", provincia="Buenos Aires", ciudad="Buenos Aires",
        servicio="Eliminación de malware / spyware", equipo="PC",
        precio_freelance=25000, precio_local=25000, moneda="ARS",
        fecha_relevamiento=date(2026, 7, 20), fuente="",
    )

    with patch("src.main.VidaInformaticaScraper") as MockVida, \
         patch("src.main.BairesCloudScraper") as MockBaires:

        MockVida.return_value.obtener_servicios.return_value = [servicio_vida]
        MockBaires.return_value.obtener_servicios.return_value = [servicio_baires]

        ejecutar(ruta_db=db_temporal)

    repo = RepositorioSQLite(db_temporal)
    empresas_guardadas = {s.empresa for s in repo.obtener_todos()}

    assert empresas_guardadas == {"Vida informatica", "BairesCloud"}