from fastapi.testclient import TestClient

from src.api.main import app


cliente = TestClient(app)


def test_consultar_servicio_filtra_por_provincia(mercado_api):

    respuesta = cliente.get(
        "/servicios/Eliminación de malware?provincia=Córdoba"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["precio_minimo"] == 29816

    empresas = [
        empresa["empresa"]
        for empresa in datos["empresas"]
    ]

    assert "Vida informatica" in empresas
