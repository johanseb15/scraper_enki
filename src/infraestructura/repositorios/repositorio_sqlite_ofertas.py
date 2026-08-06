import sqlite3
from typing import List, Optional

class RepositorioSQLiteOfertas:
    """Repositorio para la persistencia de ofertas utilizando SQLite."""

    def __init__(self, *args, **kwargs):
        # Captura cualquier argumento (ruta_db, db_path, path o posicional) de forma segura
        ruta_db = "datos.db"
        if args:
            ruta_db = args[0]
        else:
            for key in ["ruta_db", "db_path", "path", "database"]:
                if key in kwargs:
                    ruta_db = kwargs[key]
                    break

        self.ruta_db = ruta_db
        self.conexion = sqlite3.connect(self.ruta_db)
        self.conexion.row_factory = sqlite3.Row
        self._crear_tabla()

    def _crear_tabla(self):
        """Crea la tabla de ofertas si no existe para evitar errores."""
        with self.conexion:
            self.conexion.execute("""
                CREATE TABLE IF NOT EXISTS ofertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT,
                    fuente TEXT,
                    servicio TEXT,
                    precio REAL,
                    moneda TEXT,
                    provincia TEXT,
                    fecha TEXT
                )
            """)

    def __enter__(self):
        """Permite usar la clase como un context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra la conexión automáticamente al salir del bloque with."""
        self.cerrar()

    def cerrar(self):
        """Cierra la conexión a la base de datos."""
        if self.conexion:
            self.conexion.close()