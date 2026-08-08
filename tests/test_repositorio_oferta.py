from datetime import date

from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)


def test_repositorio_guarda_oferta_con_empresa_y_servicio(tmp_path):
    db_file = tmp_path / "test_enki.db"
    repo = RepositorioSQLiteOfertas(ruta_db=str(db_file))

    empresa = Empresa(
        nombre="Soporte Informático Córdoba",
        provincia="Córdoba",
        ciudad="Córdoba",
        fuente="https://soportecordoba.com",
    )
    oferta = Oferta(
        empresa=empresa,
        servicio=ServicioCanonico.MALWARE,
        precio=18000,
        moneda="ARS",
        fecha_relevamiento=date(2026, 7, 30),
    )

    repo.guardar(oferta)
    ofertas_guardadas = repo.obtener_todas()

    assert len(ofertas_guardadas) == 1
    recuperada = ofertas_guardadas[0]
    assert recuperada.empresa.nombre == "Soporte Informático Córdoba"
    assert recuperada.servicio == ServicioCanonico.MALWARE
    assert recuperada.precio == 18000
    assert recuperada.moneda == "ARS"
