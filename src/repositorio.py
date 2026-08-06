import sqlite3
from typing import Optional, List, Dict, Any

class RepositorioSQLiteOfertas:
    def __init__(self, ruta_db: Optional[str] = None, db_path: Optional[str] = None):
        """
        Acepta tanto 'ruta_db' como 'db_path' para mantener retrocompatibilidad
        con la suite de pruebas y la interfaz del dominio.
        """
        self.db_path = ruta_db or db_path or "enki.db"
        self._inicializar_tabla()

    def _obtener_conexion(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _inicializar_tabla(self) -> None:
        """Crea la tabla asegurando que exista la columna 'titulo'."""
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ofertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT,
                    precio REAL,
                    moneda TEXT,
                    servicio TEXT,
                    proveedor TEXT,
                    url TEXT
                );
            """)
            conn.commit()

    def guardar(self, oferta: Any) -> None:
        """Soporta tanto objetos DTO/Entidad como diccionarios."""
        titulo = getattr(oferta, 'titulo', None) or (oferta.get('titulo') if isinstance(oferta, dict) else '')
        precio = getattr(oferta, 'precio', None) or (oferta.get('precio') if isinstance(oferta, dict) else 0.0)
        
        # Extraer monto si precio es un objeto
        if hasattr(precio, 'monto'):
            precio_val = precio.monto
        elif hasattr(precio, 'valor'):
            precio_val = precio.valor
        else:
            precio_val = precio

        moneda = getattr(oferta, 'moneda', 'ARS') or (oferta.get('moneda', 'ARS') if isinstance(oferta, dict) else 'ARS')
        servicio = getattr(oferta, 'servicio', None) or (oferta.get('servicio') if isinstance(oferta, dict) else '')
        proveedor = getattr(oferta, 'proveedor', None) or (oferta.get('proveedor') if isinstance(oferta, dict) else '')
        url = getattr(oferta, 'url', None) or (oferta.get('url') if isinstance(oferta, dict) else '')

        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ofertas (titulo, precio, moneda, servicio, proveedor, url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (titulo, precio_val, str(moneda), str(servicio), proveedor, url))
            conn.commit()

    def obtener_todas(self) -> List[Dict[str, Any]]:
        """Consulta coincidente con las columnas del esquema."""
        with self._obtener_conexion() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT titulo, precio, moneda, servicio, proveedor, url FROM ofertas")
            filas = cursor.fetchall()
            return [dict(fila) for fila in filas]

    def obtener_todos(self) -> List[Dict[str, Any]]:
        """Alias de compatibilidad para obtener_todas()"""
        return self.obtener_todas()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Alias de compatibilidad para la suite de pruebas
RepositorioSQLite = RepositorioSQLiteOfertas