from datetime import date

from src.infraestructura.scrapers.baires_cloud import extraer_precios_bairescloud
from src.infraestructura.scrapers.base import BaseScraper
from src.infraestructura.scrapers.compragamer_parser import (
    parsear_ofertas_compragamer,
)
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.pipeline import PipelineOfertas


class ScraperConDTO(BaseScraper):
    def __init__(self, dtos):
        self.dtos = dtos

    def obtener_servicios(self):
        return self.dtos


def _ejecutar_y_recuperar(tmp_path, nombre_db, dtos):
    repositorio = RepositorioSQLiteOfertas(ruta_db=str(tmp_path / nombre_db))
    ofertas = PipelineOfertas(
        scrapers=[ScraperConDTO(dtos)],
        repositorio=repositorio,
    ).ejecutar()
    return ofertas, repositorio.obtener_todas()


def test_bairescloud_preserva_precio_raw_hasta_sqlite(tmp_path):
    dtos = extraer_precios_bairescloud(
        """
        <table>
          <tr><th>Servicio</th><th>Equipo</th><th>Precio</th></tr>
          <tbody><tr><td>Formateo</td><td>PC</td><td>$ 30.000,00</td></tr></tbody>
        </table>
        """,
        fecha_relevamiento=date(2026, 8, 9),
    )

    ofertas, persistidas = _ejecutar_y_recuperar(
        tmp_path, "baires_raw.db", dtos
    )

    assert dtos[0].precio == 30000
    assert dtos[0].precio_raw == "$ 30.000,00"
    assert ofertas[0].precio_raw == "$ 30.000,00"
    assert persistidas[0].precio.valor == 30000
    assert persistidas[0].precio_raw == "$ 30.000,00"


def test_compragamer_preserva_precio_raw_hasta_sqlite(tmp_path):
    dtos = parsear_ofertas_compragamer(
        [
            {
                "id_producto": 100,
                "nombre": "AMD Ryzen 5 5600X",
                "precioEspecial": "215000.00",
                "precioLista": "250000.00",
            }
        ],
        fecha_relevamiento=date(2026, 8, 9),
    )

    ofertas, persistidas = _ejecutar_y_recuperar(
        tmp_path, "compragamer_raw.db", dtos
    )

    assert dtos[0].precio == 215000
    assert dtos[0].precio_raw == "215000.00"
    assert ofertas[0].precio_raw == "215000.00"
    assert persistidas[0].precio.valor == 215000
    assert persistidas[0].precio_raw == "215000.00"
