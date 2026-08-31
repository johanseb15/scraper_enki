from datetime import date
from pathlib import Path
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.infraestructura.scrapers.baires_cloud import extraer_precios_bairescloud


def test_bairescloud_puede_guardarse_en_sqlite(tmp_path):
    html = Path("tests/fixtures/bairescloud.html").read_text(encoding="utf-8")
    dtos = extraer_precios_bairescloud(
        html=html, fecha_relevamiento=date(2026, 2, 1)
    )

    db_file = str(tmp_path / "test_bairescloud.db")
    with RepositorioSQLiteOfertas(ruta_db=db_file) as repositorio:
        procesador = ProcesadorOfertas(repositorio=repositorio)

        for dto in dtos:
            procesador.procesar(dto)

        ofertas_guardadas = repositorio.obtener_todas()
        assert len(ofertas_guardadas) == len(dtos)