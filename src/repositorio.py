import sqlite3
from datetime import date
from typing import List
from src.modelos.servicio_precio import ServicioPrecio


class RepositorioSQLite:

    def __init__(self, ruta_db: str = "enki.db"):
        # check_same_thread=False evita el error de SQLite al ser llamado desde FastAPI/TestClient
        self.conexion = sqlite3.connect(ruta_db, check_same_thread=False)
        self._crear_tabla()

    def _crear_tabla(self):
        self.conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS servicio_precio (
                empresa TEXT,
                provincia TEXT,
                ciudad TEXT,
                servicio TEXT,
                equipo TEXT,
                precio_freelance INTEGER,
                precio_local INTEGER,
                moneda TEXT,
                fecha_relevamiento TEXT,
                fuente TEXT,
                PRIMARY KEY (empresa, provincia, ciudad, servicio, equipo, fecha_relevamiento)
            )
            """
        )
        self.conexion.commit()

    def guardar(self, servicio: ServicioPrecio):
        nombre_servicio = (
            servicio.servicio.value
            if hasattr(servicio.servicio, "value")
            else str(servicio.servicio)
        )

        fecha_str = (
            servicio.fecha_relevamiento.isoformat()
            if hasattr(servicio.fecha_relevamiento, "isoformat")
            else str(servicio.fecha_relevamiento)
        )

        self.conexion.execute(
            """
            INSERT OR IGNORE INTO servicio_precio
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                servicio.empresa,
                servicio.provincia,
                servicio.ciudad,
                nombre_servicio,
                servicio.equipo,
                servicio.precio_freelance,
                servicio.precio_local,
                servicio.moneda,
                fecha_str,
                servicio.fuente,
            ),
        )
        self.conexion.commit()

    def obtener_todos(self) -> List[ServicioPrecio]:
        cursor = self.conexion.cursor()
        cursor.execute("SELECT * FROM servicio_precio")
        filas = cursor.fetchall()

        servicios = []
        for fila in filas:
            fecha = (
                date.fromisoformat(fila[8])
                if isinstance(fila[8], str)
                else fila[8]
            )
            servicios.append(
                ServicioPrecio(
                    empresa=fila[0],
                    provincia=fila[1],
                    ciudad=fila[2],
                    servicio=fila[3],
                    equipo=fila[4],
                    precio_freelance=fila[5],
                    precio_local=fila[6],
                    moneda=fila[7],
                    fecha_relevamiento=fecha,
                    fuente=fila[9],
                )
            )
        return servicios
