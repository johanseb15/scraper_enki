from pathlib import Path
from unittest.mock import patch
import pytest
from src.main import ejecutar
from src.extractor import extraer_datos

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