from datetime import date

from fastapi.testclient import TestClient

from src.api.main import app, obtener_repositorio
from src.modelos.servicio_precio import ServicioPrecio
from src.repositorio import RepositorioSQLite


cliente = TestClient(app)


def test_consultar_servicio_devuelve_estadisticas():
    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["servicio"] == "Eliminación de malware"
    assert datos["precio_minimo"] == 29816
    assert datos["precio_promedio"] == 33862
    assert datos["precio_maximo"] == 46000


def test_consultar_servicio_usa_datos_reales_del_repositorio(tmp_path):
    ruta_db = str(tmp_path / "test_enki.db")

    repo = RepositorioSQLite(ruta_db)

    repo.guardar(
        ServicioPrecio(
            empresa="Empresa Test A",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=10000,
            precio_local=10000,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="test",
        )
    )

    repo.guardar(
        ServicioPrecio(
            empresa="Empresa Test B",
            provincia="Buenos Aires",
            ciudad="Buenos Aires",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=20000,
            precio_local=20000,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="test",
        )
    )

    app.dependency_overrides[obtener_repositorio] = lambda: repo

    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    app.dependency_overrides.clear()

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["precio_minimo"] == 10000
    assert datos["precio_maximo"] == 20000
    assert datos["precio_promedio"] == 15000

def test_consultar_servicio_devuelve_empresas():
    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert "empresas" in datos

def test_consultar_servicio_devuelve_ciudades():

    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert "ciudades" in datos
    assert "Córdoba" in datos["ciudades"]