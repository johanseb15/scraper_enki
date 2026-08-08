from pathlib import Path

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico
from src.extractor import extraer_datos
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.presentacion import generar_reporte_texto
from src.reporte import generar_resumen_servicio


def test_pipeline_completo_de_html_a_reporte(tmp_path):
    ruta_html = Path(__file__).parent / "fixtures" / "vida_informatica_zona1.html"
    html = ruta_html.read_text(encoding="utf-8")
    dtos = extraer_datos(html)
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "procesador_reporte.db")
    )
    procesador = ProcesadorOfertas(repositorio=repositorio)

    ofertas = procesador.ejecutar(dtos)
    persistidas = repositorio.obtener_todas()
    resumen = generar_resumen_servicio(
        persistidas,
        "Eliminación de malware",
    )
    reporte = generar_reporte_texto(resumen)

    assert all(isinstance(dto, OfertaDTO) for dto in dtos)
    assert all(isinstance(oferta, Oferta) for oferta in ofertas)
    assert len(persistidas) == len(ofertas)
    assert any(
        oferta.servicio == ServicioCanonico.MALWARE
        and oferta.servicio_raw == "Eliminación de malware"
        and oferta.precio.valor == 29816
        for oferta in persistidas
    )
    assert "Eliminación de malware" in reporte
    assert "29816" in reporte
