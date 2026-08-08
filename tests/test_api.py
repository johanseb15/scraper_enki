from datetime import date

from fastapi.testclient import TestClient

from src.api.main import app, obtener_repositorio
from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)


cliente = TestClient(app)


def test_consultar_servicio_devuelve_estadisticas(mercado_api):
    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["servicio"] == "Eliminación de malware"
    assert datos["precio_minimo"] == 29816
    assert datos["precio_promedio"] == 37908
    assert datos["precio_maximo"] == 46000


def test_consultar_servicio_usa_datos_reales_del_repositorio(tmp_path):
    ruta_db = str(tmp_path / "test_enki.db")

    repo = RepositorioSQLiteOfertas(ruta_db=ruta_db)

    repo.guardar(
        Oferta(
            empresa=Empresa(
                nombre="Empresa Test A",
                provincia="Córdoba",
                ciudad="Córdoba",
                fuente="test",
            ),
            servicio=ServicioCanonico.MALWARE,
            servicio_raw="Eliminación de malware",
            precio=10000,
            modalidad="local",
            precio_raw="$ 10.000",
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
        )
    )

    repo.guardar(
        Oferta(
            empresa=Empresa(
                nombre="Empresa Test B",
                provincia="Buenos Aires",
                ciudad="Buenos Aires",
                fuente="test",
            ),
            servicio=ServicioCanonico.MALWARE,
            servicio_raw="Eliminación de malware",
            precio=20000,
            modalidad="local",
            precio_raw="$ 20.000",
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
        )
    )

    app.dependency_overrides[obtener_repositorio] = lambda: repo
    try:
        respuesta = cliente.get(
            "/servicios/Eliminación de malware"
        )
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["precio_minimo"] == 10000
    assert datos["precio_maximo"] == 20000
    assert datos["precio_promedio"] == 15000

def test_consultar_servicio_devuelve_empresas(mercado_api):

    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert "empresas" in datos

    empresas = [
        empresa["empresa"]
        for empresa in datos["empresas"]
    ]

    assert "Vida informatica" in empresas
    assert "BairesCloud" in empresas


def test_consultar_servicio_devuelve_ciudades(mercado_api):

    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert "ciudades" in datos

    assert "Córdoba" in datos["ciudades"]
