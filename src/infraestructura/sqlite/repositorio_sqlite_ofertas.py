import sqlite3
from datetime import date
from typing import List, Optional

from src.aplicacion.puertos.repositorio_ofertas import RepositorioOfertas
from src.dominio.empresa import Empresa
from src.normalizadores.normalizador_servicios import NormalizadorServicios
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico


class RepositorioSQLiteOfertas(RepositorioOfertas):

    def __init__(self, ruta_db: str = "enki.db"):
        self.ruta_db = ruta_db
        self.conexion: Optional[sqlite3.Connection] = sqlite3.connect(
            ruta_db,
            check_same_thread=False,
        )
        self._crear_tablas()

    def _crear_tablas(self) -> None:
        if not self.conexion:
            return

        with self.conexion:
            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE,
                    provincia TEXT,
                    ciudad TEXT,
                    fuente TEXT
                )
                """
            )

            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS ofertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER,
                    servicio TEXT,
                    precio INTEGER,
                    moneda TEXT,
                    fecha_relevamiento TEXT,
                    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
                )
                """
            )

    def guardar(self, oferta: Oferta) -> None:
        if not self.conexion:
            raise RuntimeError("La conexión a la base de datos está cerrada.")

        with self.conexion:
            cursor = self.conexion.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO empresas
                (nombre, provincia, ciudad, fuente)
                VALUES (?, ?, ?, ?)
                """,
                (
                    oferta.empresa.nombre,
                    oferta.empresa.provincia,
                    oferta.empresa.ciudad,
                    oferta.empresa.fuente,
                ),
            )

            cursor.execute(
                "SELECT id FROM empresas WHERE nombre = ?",
                (oferta.empresa.nombre,),
            )

            resultado = cursor.fetchone()
            if not resultado:
                raise ValueError(f"No se pudo registrar o encontrar la empresa {oferta.empresa.nombre}")
            
            empresa_id = resultado[0]

            cursor.execute(
                """
                INSERT INTO ofertas
                (empresa_id, servicio, precio, moneda, fecha_relevamiento)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    empresa_id,
                    oferta.servicio.value,
                    oferta.precio,
                    oferta.moneda,
                    oferta.fecha_relevamiento.isoformat(),
                ),
            )

    def obtener_todas(self) -> List[Oferta]:
        if not self.conexion:
            raise RuntimeError("La conexión a la base de datos está cerrada.")

        cursor = self.conexion.cursor()

        cursor.execute(
            """
            SELECT
                e.nombre,
                e.provincia,
                e.ciudad,
                e.fuente,
                o.servicio,
                o.precio,
                o.moneda,
                o.fecha_relevamiento
            FROM ofertas o
            JOIN empresas e
              ON o.empresa_id = e.id
            """
        )

        filas = cursor.fetchall()

        normalizador = NormalizadorServicios()
        ofertas: List[Oferta] = []

        for fila in filas:
            empresa = Empresa(
                nombre=fila[0],
                provincia=fila[1],
                ciudad=fila[2],
                fuente=fila[3],
            )

            try:
                servicio = ServicioCanonico(fila[4])
            except ValueError:
                servicio = normalizador.normalizar(fila[4])

            ofertas.append(
                Oferta(
                    empresa=empresa,
                    servicio=servicio,
                    precio=fila[5],
                    moneda=fila[6],
                    fecha_relevamiento=date.fromisoformat(fila[7]),
                )
            )

        return ofertas

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