from datetime import date

from fastapi.testclient import TestClient

from src.api.main import app, obtener_repositorio
from src.repositorio import RepositorioSQLite
from src.modelos.servicio_precio import ServicioPrecio


cliente = TestClient(app)


def crear_repositorio_api():

    repo = RepositorioSQLite(":memory:")

    repo.guardar(
        ServicioPrecio(
            empresa="Vida informatica",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=29816,
            precio_local=41411,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="test",
        )
    )

    repo.guardar(
        ServicioPrecio(
            empresa="BairesCloud",
            provincia="Buenos Aires",
            ciudad="Buenos Aires",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=46000,
            precio_local=46000,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="test",
        )
    )

    return repo


def preparar_api():

    repo = crear_repositorio_api()

    app.dependency_overrides[obtener_repositorio] = (
        lambda: repo
    )

    return repo


def limpiar_api():

    app.dependency_overrides.clear()


def test_consultar_servicio_devuelve_estadisticas():

    preparar_api()

    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["servicio"] == "Eliminación de malware"
    assert datos["precio_minimo"] == 29816
    assert datos["precio_promedio"] == 37908
    assert datos["precio_maximo"] == 46000

    limpiar_api()


def test_consultar_servicio_usa_datos_reales_del_repositorio():

    repo = RepositorioSQLite(":memory:")

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

    app.dependency_overrides[obtener_repositorio] = (
        lambda: repo
    )

    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    datos = respuesta.json()

    assert datos["precio_minimo"] == 10000
    assert datos["precio_maximo"] == 20000
    assert datos["precio_promedio"] == 15000

    limpiar_api()


def test_consultar_servicio_devuelve_empresas():

    preparar_api()

    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    datos = respuesta.json()

    assert "empresas" in datos

    empresas = [
        empresa["empresa"]
        for empresa in datos["empresas"]
    ]

    assert "Vida informatica" in empresas
    assert "BairesCloud" in empresas

    limpiar_api()


def test_consultar_servicio_devuelve_ciudades():

    preparar_api()

    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    datos = respuesta.json()

    assert "ciudades" in datos

    assert "Córdoba" in datos["ciudades"]
    assert "Buenos Aires" in datos["ciudades"]

    limpiar_api()
