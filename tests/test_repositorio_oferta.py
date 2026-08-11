import sqlite3
from datetime import date

from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta, PrecioValor
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


def test_repositorio_preserva_periodo_del_precio(tmp_path):
    db_file = tmp_path / "test_enki_periodo.db"
    repo = RepositorioSQLiteOfertas(ruta_db=str(db_file))

    empresa = Empresa(
        nombre="Soporte Informatico Cordoba",
        provincia="Cordoba",
        ciudad="Cordoba",
        fuente="https://soportecordoba.com",
    )
    oferta = Oferta(
        empresa=empresa,
        servicio=ServicioCanonico.MALWARE,
        precio=PrecioValor(valor=350000, moneda="ARS", periodo="mes"),
        moneda="ARS",
        fecha_relevamiento=date(2026, 8, 11),
    )

    repo.guardar(oferta)
    recuperada = repo.obtener_todas()[0]

    assert recuperada.precio.valor == 350000
    assert recuperada.precio.moneda == "ARS"
    assert recuperada.precio.periodo == "mes"


def test_repositorio_migra_tabla_legacy_sin_inventar_periodo(tmp_path):
    db_file = tmp_path / "legacy_sin_periodo.db"
    with sqlite3.connect(db_file) as conexion:
        conexion.execute(
            """
            CREATE TABLE ofertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa TEXT,
                fuente TEXT,
                servicio TEXT,
                precio REAL,
                moneda TEXT,
                provincia TEXT,
                ciudad TEXT,
                fecha_relevamiento TEXT,
                servicio_raw TEXT,
                modalidad TEXT,
                precio_raw TEXT
            )
            """
        )
        conexion.execute(
            """
            INSERT INTO ofertas (
                empresa, fuente, servicio, precio, moneda, provincia, ciudad,
                fecha_relevamiento, servicio_raw, modalidad, precio_raw
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Legacy",
                "https://legacy.example",
                ServicioCanonico.MALWARE.value,
                120000,
                "ARS",
                "Cordoba",
                "Cordoba",
                "2026-08-11",
                "Eliminacion de malware",
                None,
                "$120.000",
            ),
        )

    repo = RepositorioSQLiteOfertas(ruta_db=str(db_file))
    recuperada = repo.obtener_todas()[0]

    assert recuperada.precio.valor == 120000
    assert recuperada.precio.moneda == "ARS"
    assert recuperada.precio.periodo is None
