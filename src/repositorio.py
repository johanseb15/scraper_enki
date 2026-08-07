# src/repositorio.py

import sqlite3
from typing import Any


class RepositorioSQLiteOfertas:
    """
    Repositorio SQLite para persistencia de ofertas.

    Durante la migración mantiene compatibilidad con la antigua clase
    RepositorioSQLite mediante un alias al final del archivo.
    """

    def __init__(self, ruta_db: str = "enki.db"):
        self.ruta_db = ruta_db
        self._inicializar_tabla()

    def _obtener_conexion(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.ruta_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_tabla(self) -> None:
        """Crea la tabla si no existe."""
        with self._obtener_conexion() as conn:
            conn.execute(
                """
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
                """
            )
            conn.commit()

    def guardar(self, oferta: Any) -> None:
        """Guarda una oferta (dict o DTO/entidad)."""

        if isinstance(oferta, dict):
            titulo = oferta.get("titulo") or oferta.get("servicio", "")

            precio_obj = oferta.get("precio", 0.0)
            if hasattr(precio_obj, "valor"):
                precio = precio_obj.valor
            else:
                try:
                    precio = float(precio_obj)
                except (TypeError, ValueError):
                    precio = 0.0

            moneda = oferta.get("moneda", "ARS")
            servicio = oferta.get("servicio", "")
            proveedor = oferta.get("empresa") or oferta.get("proveedor", "")
            url = oferta.get("url", "")
            provincia = oferta.get("provincia", "")
            ciudad = oferta.get("ciudad", "")
            fecha = oferta.get("fecha_relevamiento")

        else:
            titulo = getattr(oferta, "titulo", None) or getattr(
                oferta, "servicio", ""
            )

            precio_obj = getattr(oferta, "precio", 0.0)
            precio = (
                precio_obj.valor
                if hasattr(precio_obj, "valor")
                else float(precio_obj)
            )

            moneda = getattr(oferta, "moneda", "ARS")
            servicio = getattr(oferta, "servicio", "")
            proveedor = getattr(
                oferta,
                "proveedor",
                getattr(oferta, "empresa", "")
            )
            url = getattr(oferta, "url", "")
            provincia = getattr(oferta, "provincia", "")
            ciudad = getattr(oferta, "ciudad", "")
            fecha = getattr(oferta, "fecha_relevamiento", None)

        with self._obtener_conexion() as conn:
            conn.execute(
                """
                INSERT INTO ofertas (
                    titulo,
                    precio,
                    moneda,
                    servicio,
                    proveedor,
                    url,
                    provincia,
                    ciudad,
                    fecha_relevamiento
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    titulo,
                    precio,
                    moneda,
                    servicio,
                    proveedor,
                    url,
                    provincia,
                    ciudad,
                    fecha,
                ),
            )
            conn.commit()

    def obtener_todas(self) -> list[dict[str, Any]]:
        """Obtiene todas las ofertas."""

        with self._obtener_conexion() as conn:
            cursor = conn.execute(
                """
                SELECT
                    titulo,
                    precio,
                    moneda,
                    servicio,
                    proveedor,
                    url,
                    provincia,
                    ciudad,
                    fecha_relevamiento
                FROM ofertas
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    # =====================================================
    # Compatibilidad con el código legacy
    # =====================================================

    def obtener_todos(self):
        """
        Alias temporal para compatibilidad con código antiguo.
        """
        return self.obtener_todas()


# ==========================================================
# Alias temporal de compatibilidad.
# Eliminar cuando toda la aplicación utilice
# RepositorioSQLiteOfertas.
# ==========================================================

RepositorioSQLite = RepositorioSQLiteOfertas