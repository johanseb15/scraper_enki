import pytest
from src.infraestructura.repositorios import RepositorioSQLite

@pytest.fixture
def repositorio_db():
    """Proporciona una instancia de RepositorioSQLite en memoria que se cierra automáticamente."""
    repo = RepositorioSQLite(ruta_db=":memory:")
    yield repo
    repo.cerrar()