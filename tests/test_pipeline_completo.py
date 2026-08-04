from pathlib import Path

from src.extractor import extraer_datos
from src.repositorio import RepositorioSQLite
from src.reporte import generar_resumen_servicio
from src.presentacion import generar_reporte_texto


def test_pipeline_completo_de_html_a_reporte():
    ruta_html = Path(__file__).parent / "fixtures" / "vida_informatica_zona1.html"
    html = ruta_html.read_text(encoding="utf-8")

    filas = extraer_datos(html)

    with RepositorioSQLite(":memory:") as repositorio:
        for fila in filas:
            repositorio.guardar(fila)

        datos_guardados = repositorio.obtener_todos()

    resumen = generar_resumen_servicio(datos_guardados, "Eliminación de malware")
    reporte = generar_reporte_texto(resumen)

    assert "Eliminación de malware" in reporte
    assert "29" in reporte