from fastapi.testclient import TestClient
from src.api.main import app, obtener_repositorio
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)

cliente = TestClient(app)

def test_consultar_servicio_devuelve_estadisticas(tmp_path):
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "api_estructura.db")
    )
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio

    # Petición HTTP al endpoint con codificación correcta
    try:
        respuesta = cliente.get("/servicios/Eliminacion de malware")
    finally:
        app.dependency_overrides.clear()
    
    # Assert sobre el resultado HTTP
    assert respuesta.status_code == 200
    
    # Assert sobre la estructura JSON del resultado
    datos = respuesta.json()
    assert "servicio" in datos
