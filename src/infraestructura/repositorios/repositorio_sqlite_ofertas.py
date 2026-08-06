from src.repositorio import RepositorioSQLite


class RepositorioSQLiteOfertas(RepositorioSQLite):
    """Adaptador de infraestructura que extiende la funcionalidad base de RepositorioSQLite."""

    def __init__(self, ruta_db: str = "enki.db"):
        super().__init__(db_path=ruta_db)