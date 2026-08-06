class RepositorioSQLiteOfertas:
    def __init__(self, ruta_db: str = "enki.db", db_path: str = None):
        self.ruta_db = db_path or ruta_db