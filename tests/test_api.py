from fastapi.testclient import TestClient
from src.api.main import app


cliente = TestClient(app)


def test_consultar_servicio_devuelve_estadisticas():
    respuesta = cliente.get(
        "/servicios/Eliminación de malware"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["precio_promedio"] == 33862