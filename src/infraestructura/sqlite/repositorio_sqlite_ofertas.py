import sqlite3
from datetime import date
from typing import List

from src.aplicacion.puertos.repositorio_ofertas import RepositorioOfertas
from src.dominio.empresa import Empresa
from src.dominio.normalizador_servicios import NormalizadorServicios
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico


class RepositorioSQLiteOfertas(RepositorioOfertas):

    def __init__(self, ruta_db: str = "enki.db"):
        self.conexion = sqlite3.connect(
            ruta_db,
            check_same_thread=False,
        )
        self._crear_tablas()

    def _crear_tablas(self) -> None:
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

        self.conexion.commit()

    def guardar(self, oferta: Oferta) -> None:
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

        empresa_id = cursor.fetchone()[0]

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

        self.conexion.commit()

    def obtener_todas(self) -> List[Oferta]:
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
        self.conexion.close()