from fastapi.testclient import TestClient
from src.api.main import app

cliente = TestClient(app)

def test_consultar_servicio_devuelve_estadisticas():
    # Petición HTTP al endpoint con codificación correcta
    respuesta = cliente.get("/servicios/Eliminacion de malware")
    
    # Assert sobre el resultado HTTP
    assert respuesta.status_code == 200
    
    # Assert sobre la estructura JSON del resultado
    datos = respuesta.json()
    assert "servicio" in datos