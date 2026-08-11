import sqlite3
from dataclasses import replace
from datetime import date

from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta, PrecioValor
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)


def _crear_observacion(**cambios) -> Oferta:
    oferta = Oferta(
        empresa=Empresa(
            nombre="Soporte Informatico Cordoba",
            provincia="Cordoba",
            ciudad="Cordoba",
            fuente="https://soportecordoba.com/ofertas/malware",
        ),
        servicio=ServicioCanonico.MALWARE,
        precio=PrecioValor(valor=50000, moneda="ARS"),
        moneda="ARS",
        fecha_relevamiento=date(2026, 8, 11),
        servicio_raw="Eliminacion de malware",
        modalidad="local",
        precio_raw="$50.000",
    )
    return replace(oferta, **cambios)


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


def test_repositorio_no_duplica_la_misma_observacion(tmp_path):
    db_file = tmp_path / "test_enki_idempotencia.db"
    repo = RepositorioSQLiteOfertas(ruta_db=str(db_file))
    oferta = _crear_observacion()

    repo.guardar(oferta)
    repo.guardar(oferta)

    assert len(repo.obtener_todas()) == 1


def test_repositorio_conserva_la_misma_oferta_en_otra_fecha(tmp_path):
    repo = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "test_enki_revision.db")
    )

    repo.guardar(_crear_observacion())
    repo.guardar(
        _crear_observacion(fecha_relevamiento=date(2026, 8, 12))
    )

    assert len(repo.obtener_todas()) == 2


def test_repositorio_no_mezcla_proveedores_distintos(tmp_path):
    repo = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "test_enki_proveedores.db")
    )
    otra_empresa = Empresa(
        nombre="Otro Proveedor",
        provincia="Cordoba",
        ciudad="Cordoba",
        fuente="https://otro.example/ofertas/malware",
    )

    repo.guardar(_crear_observacion())
    repo.guardar(_crear_observacion(empresa=otra_empresa))

    assert len(repo.obtener_todas()) == 2


def test_repositorio_reabierto_mantiene_la_idempotencia(tmp_path):
    ruta_db = str(tmp_path / "test_enki_reapertura.db")
    RepositorioSQLiteOfertas(ruta_db=ruta_db).guardar(_crear_observacion())

    repo_reabierto = RepositorioSQLiteOfertas(ruta_db=ruta_db)
    repo_reabierto.guardar(_crear_observacion())

    assert len(repo_reabierto.obtener_todas()) == 1


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

    repo.guardar(recuperada)

    assert len(repo.obtener_todas()) == 1
