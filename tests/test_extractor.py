from pathlib import Path

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.dominio.servicios import ServicioCanonico
from src.extractor import extraer_datos


def test_extrae_filas_de_la_tabla_de_datos():
    # Leer el HTML de prueba
    ruta_html = Path(__file__).parent / "fixtures" / "vida_informatica_zona1.html"
    html = ruta_html.read_text(encoding="utf-8")

    # Ejecutar el extractor
    resultados = extraer_datos(html)

    # Debe haber más de 10 filas
    assert len(resultados) > 10

    # Verificar que la primera fila tenga las claves esperadas
    primera = resultados[0]

    assert isinstance(primera, OfertaDTO)
    assert primera.servicio_raw != ""
    assert primera.precio is not None
    assert primera.precio > 0

    # Buscar la fila correspondiente a Malware utilizando el Enum canónico
    fila_malware = next(
        r for r in resultados if r.servicio_raw.lower().find("malware") >= 0
    )

    assert fila_malware.precio == 29816
