# src/repositorio.py

import sqlite3
from typing import List, Dict, Any, Optional

class RepositorioSQLiteOfertas:
    def __init__(self, ruta_db: str):
        self.ruta_db = ruta_db
        self._inicializar_tabla()

    def _obtener_conexion(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.ruta_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_tabla(self) -> None:
        """Crea la tabla de ofertas si no existe para prevenir errores de tablas ausentes."""
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
                    url TEXT,
                    provincia TEXT,
                    ciudad TEXT,
                    fecha_relevamiento TEXT
                )
            """)
            conn.commit()

    def obtener_todas(self) -> List[Dict[str, Any]]:
        """Recupera todas las ofertas almacenadas en la base de datos."""
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT titulo, precio, moneda, servicio, proveedor, url, provincia, ciudad, fecha_relevamiento FROM ofertas")
            return [dict(row) for row in cursor.fetchall()]

    def guardar(self, oferta: Any) -> None:
        """Inserta una oferta o un diccionario de datos procesados en la base de datos."""
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Soporte dual: si es un diccionario o un objeto/DTO con atributos
            if isinstance(oferta, dict):
                titulo = oferta.get('titulo') or oferta.get('servicio', '')
                
                # Manejo del precio si viene como objeto o flotante
                precio_val = oferta.get('precio', 0.0)
                if hasattr(precio_val, 'valor'):
                    precio = precio_val.valor
                else:
                    try:
                        precio = float(precio_val)
                    except (ValueError, TypeError):
                        precio = 0.0

                moneda = oferta.get('moneda', 'ARS')
                servicio = oferta.get('servicio', '')
                proveedor = oferta.get('empresa') or oferta.get('proveedor', '')
                url = oferta.get('url', '')
                provincia = oferta.get('provincia', '')
                ciudad = oferta.get('ciudad', '')
                fecha_relevamiento = oferta.get('fecha_relevamiento', None)
            else:
                titulo = getattr(oferta, 'titulo', None) or getattr(oferta, 'servicio', '')
                p_obj = getattr(oferta, 'precio', 0.0)
                precio = p_obj.valor if hasattr(p_obj, 'valor') else float(p_obj)
                moneda = getattr(oferta, 'moneda', 'ARS')
                servicio = getattr(oferta, 'servicio', '')
                proveedor = getattr(oferta, 'proveedor', None) or getattr(oferta, 'empresa', '')
                url = getattr(oferta, 'url', '')
                provincia = getattr(oferta, 'provincia', '')
                ciudad = getattr(oferta, 'ciudad', '')
                fecha_relevamiento = getattr(oferta, 'fecha_relevamiento', None)

            cursor.execute("""
                INSERT INTO ofertas (titulo, precio, moneda, servicio, proveedor, url, provincia, ciudad, fecha_relevamiento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (titulo, precio, moneda, servicio, proveedor, url, provincia, ciudad, fecha_relevamiento))
            conn.commit()