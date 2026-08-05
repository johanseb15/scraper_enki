"""Repositorio SQLite para la persistencia de ofertas en scraper_enki."""

import logging
import sqlite3
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RepositorioSQLiteOfertas:
    """Maneja el almacenamiento y consulta de ofertas en SQLite."""

    def __init__(self, db_path: str = "enki.db"):
        self.db_path = db_path
        self._crear_tabla()

    def _get_connection(self) -> sqlite3.Connection:
        """Retorna una conexión a la base de datos SQLite."""
        return sqlite3.connect(self.db_path)

    def _crear_tabla(self) -> None:
        """Crea la tabla 'ofertas' si no existe en el esquema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ofertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    titulo_raw TEXT,
                    precio REAL,
                    moneda TEXT DEFAULT 'ars',
                    url TEXT,
                    proveedor TEXT,
                    categoria_normalizada TEXT DEFAULT 'General',
                    subcategoria_normalizada TEXT DEFAULT 'otros',
                    fecha_relevamiento TEXT
                )
            """)
            conn.commit()

    def _extraer_campos(self, oferta: Any) -> Tuple[str, str, float, str, str, str, str, str, str]:
        """Extrae y sanitiza defensivamente los atributos de un DTO, dict u objeto."""
        if isinstance(oferta, dict):
            nombre = oferta.get("nombre") or oferta.get("servicio_raw") or oferta.get("titulo") or "Oferta"
            titulo_raw = oferta.get("titulo_raw") or oferta.get("servicio_raw") or nombre
            precio = float(oferta.get("precio", 0.0))
            moneda = str(oferta.get("moneda", "ars")).lower()
            url = str(oferta.get("url", ""))
            proveedor = str(
                oferta.get("proveedor")
                or oferta.get("empresa_nombre")
                or oferta.get("fuente")
                or "CompraGamer"
            )
            cat_norm = oferta.get("categoria_normalizada", "General")
            subcat_norm = oferta.get("subcategoria_normalizada", "otros")
            fecha = str(oferta.get("fecha_relevamiento") or date.today().isoformat())
        else:
            nombre = (
                getattr(oferta, "nombre", None)
                or getattr(oferta, "servicio_raw", None)
                or getattr(oferta, "_servicio_raw", None)
                or getattr(oferta, "titulo", "Oferta")
            )
            titulo_raw = (
                getattr(oferta, "titulo_raw", None)
                or getattr(oferta, "servicio_raw", None)
                or getattr(oferta, "_servicio_raw", nombre)
            )
            precio = float(
                getattr(oferta, "precio", None)
                or getattr(oferta, "_precio", 0.0)
            )
            moneda = str(
                getattr(oferta, "moneda", None)
                or getattr(oferta, "_moneda", "ars")
            ).lower()
            url = str(getattr(oferta, "url", ""))
            proveedor = str(
                getattr(oferta, "proveedor", None)
                or getattr(oferta, "empresa_nombre", None)
                or getattr(oferta, "_empresa_nombre", None)
                or getattr(oferta, "fuente", "CompraGamer")
            )
            cat_norm = getattr(oferta, "categoria_normalizada", "General")
            subcat_norm = getattr(oferta, "subcategoria_normalizada", "otros")
            fecha = str(
                getattr(oferta, "fecha_relevamiento", None)
                or getattr(oferta, "_fecha_relevamiento", date.today().isoformat())
            )

        # Sanitización defensiva de categorias
        cat_str = str(cat_norm) if cat_norm is not None else "General"
        subcat_str = str(subcat_norm) if subcat_norm is not None else "otros"

        # Si subcategoria recibió un objeto stringificado, forzar valor limpio
        if subcat_str.lower().startswith("ofertadto") or "(" in subcat_str:
            subcat_str = "otros"

        if cat_str.lower().startswith("ofertadto") or "(" in cat_str:
            cat_str = "General"

        return (
            str(nombre),
            str(titulo_raw),
            precio,
            moneda,
            url,
            proveedor,
            cat_str,
            subcat_str,
            fecha,
        )

    def guardar(self, oferta: Any) -> Optional[int]:
        """Guarda un registro de oferta individual."""
        campos = self._extraer_campos(oferta)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ofertas (
                    nombre, titulo_raw, precio, moneda, url,
                    proveedor, categoria_normalizada, subcategoria_normalizada, fecha_relevamiento
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, campos)
            conn.commit()
            return cursor.lastrowid

    def guardar_muchas(self, ofertas: List[Any]) -> int:
        """Inserta múltiples ofertas eficientemente en una sola transacción."""
        if not ofertas:
            return 0

        registros = [self._extraer_campos(o) for o in ofertas]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO ofertas (
                    nombre, titulo_raw, precio, moneda, url,
                    proveedor, categoria_normalizada, subcategoria_normalizada, fecha_relevamiento
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, registros)
            conn.commit()
            return cursor.rowcount

    def obtener_todas(self) -> List[Dict[str, Any]]:
        """Devuelve todas las ofertas almacenadas como diccionarios."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ofertas")
            return [dict(row) for row in cursor.fetchall()]

    def limpiar_tabla(self) -> int:
        """Borra el contenido de la tabla ofertas."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ofertas")
            conn.commit()
            return cursor.rowcount