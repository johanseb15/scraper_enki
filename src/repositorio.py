import sqlite3
from datetime import date

from src.modelos.servicio_precio import ServicioPrecio


class RepositorioSQLite:

    def __init__(self, ruta_db: str):
        self.conexion = sqlite3.connect(
            ruta_db,
            check_same_thread=False
        )

        self._crear_tabla()

    def _crear_tabla(self):

        self.conexion.execute("""
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

                UNIQUE (
                    empresa,
                    provincia,
                    ciudad,
                    servicio,
                    equipo,
                    fecha_relevamiento
                )
            )
        """)

        self.conexion.commit()

    def guardar(self, servicio: ServicioPrecio):

        self.conexion.execute(
            """
            INSERT OR IGNORE INTO servicio_precio
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                servicio.empresa,
                servicio.provincia,
                servicio.ciudad,
                servicio.servicio,
                servicio.equipo,
                servicio.precio_freelance,
                servicio.precio_local,
                servicio.moneda,
                servicio.fecha_relevamiento.isoformat(),
                servicio.fuente,
            ),
        )

        self.conexion.commit()

    def obtener_todos(self) -> list[ServicioPrecio]:

        cursor = self.conexion.execute("""
            SELECT
                empresa,
                provincia,
                ciudad,
                servicio,
                equipo,
                precio_freelance,
                precio_local,
                moneda,
                fecha_relevamiento,
                fuente
            FROM servicio_precio
        """)

        resultados = []

        for fila in cursor.fetchall():

            resultados.append(
                ServicioPrecio(
                    empresa=fila[0],
                    provincia=fila[1],
                    ciudad=fila[2],
                    servicio=fila[3],
                    equipo=fila[4],
                    precio_freelance=fila[5],
                    precio_local=fila[6],
                    moneda=fila[7],
                    fecha_relevamiento=date.fromisoformat(fila[8]),
                    fuente=fila[9],
                )
            )

        return resultados