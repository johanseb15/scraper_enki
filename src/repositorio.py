import sqlite3
from datetime import date
from typing import List, Optional
from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.modelos.servicio_precio import ServicioPrecio


class RepositorioSQLite:

    def __init__(self, ruta_db: str = "enki.db"):
        self.ruta_db = ruta_db
        # check_same_thread=False evita el error de SQLite al ser llamado desde FastAPI/TestClient
        self.conexion: Optional[sqlite3.Connection] = sqlite3.connect(
            ruta_db, check_same_thread=False
        )
        self._crear_tabla()

    def _crear_tabla(self) -> None:
        if not self.conexion:
            return

        with self.conexion:
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

    def guardar(self, servicio) -> None:
        if not self.conexion:
            raise RuntimeError("La conexión a la base de datos se encuentra cerrada.")

        if isinstance(servicio, OfertaDTO):
            nombre_servicio = servicio.servicio_raw
            equipo = ""
            precio_freelance = servicio.precio
            precio_local = servicio.precio
            fecha_str = (
                servicio.fecha_relevamiento.isoformat()
                if hasattr(servicio.fecha_relevamiento, "isoformat")
                else str(servicio.fecha_relevamiento)
            )
            empresa = servicio.empresa_nombre
            provincia = servicio.provincia
            ciudad = servicio.ciudad
            fuente = servicio.fuente
            moneda = servicio.moneda
        else:
            nombre_servicio = (
                servicio.servicio.value
                if hasattr(servicio.servicio, "value")
                else str(servicio.servicio)
            )
            equipo = servicio.equipo
            precio_freelance = servicio.precio_freelance
            precio_local = servicio.precio_local
            fecha_str = (
                servicio.fecha_relevamiento.isoformat()
                if hasattr(servicio.fecha_relevamiento, "isoformat")
                else str(servicio.fecha_relevamiento)
            )
            empresa = servicio.empresa
            provincia = servicio.provincia
            ciudad = servicio.ciudad
            fuente = servicio.fuente
            moneda = servicio.moneda

        with self.conexion:
            self.conexion.execute(
                """
                INSERT OR IGNORE INTO servicio_precio
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    empresa,
                    provincia,
                    ciudad,
                    nombre_servicio,
                    equipo,
                    precio_freelance,
                    precio_local,
                    moneda,
                    fecha_str,
                    fuente,
                ),
            )

    def obtener_todos(self) -> List[ServicioPrecio]:
        if not self.conexion:
            raise RuntimeError("La conexión a la base de datos se encuentra cerrada.")

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

    def cerrar(self) -> None:
        if self.conexion:
            self.conexion.close()
            self.conexion = None

    def close(self) -> None:
        self.cerrar()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar()