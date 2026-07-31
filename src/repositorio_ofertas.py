import sqlite3
from datetime import date
from typing import List
from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico


class RepositorioSQLiteOfertas:

    def __init__(self, ruta_db: str = "enki.db"):
        # check_same_thread=False evita errores al interactuar con hilos/FastAPI
        self.conexion = sqlite3.connect(ruta_db, check_same_thread=False)
        self._crear_tablas()

    def _crear_tablas(self):
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
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
            )
            """
        )
        self.conexion.commit()

    def guardar(self, oferta: Oferta):
        cursor = self.conexion.cursor()
        
        # 1. Asegurar o buscar la empresa para relacionarla
        cursor.execute(
            """
            INSERT OR IGNORE INTO empresas (nombre, provincia, ciudad, fuente)
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
            "SELECT id FROM empresas WHERE nombre = ?", (oferta.empresa.nombre,)
        )
        empresa_id = cursor.fetchone()[0]

        # 2. Guardar la oferta vinculada a la empresa
        nombre_servicio = (
            oferta.servicio.value
            if hasattr(oferta.servicio, "value")
            else str(oferta.servicio)
        )
        fecha_str = oferta.fecha_relevamiento.isoformat()

        cursor.execute(
            """
            INSERT INTO ofertas (empresa_id, servicio, precio, moneda, fecha_relevamiento)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                empresa_id,
                nombre_servicio,
                oferta.precio,
                oferta.moneda,
                fecha_str,
            ),
        )
        self.conexion.commit()

    def obtener_todas(self) -> List[Oferta]:
        cursor = self.conexion.cursor()
        cursor.execute(
            """
            SELECT e.nombre, e.provincia, e.ciudad, e.fuente,
                   o.servicio, o.precio, o.moneda, o.fecha_relevamiento
            FROM ofertas o
            JOIN empresas e ON o.empresa_id = e.id
            """
        )
        filas = cursor.fetchall()
        
        ofertas = []
        for fila in filas:
            empresa = Empresa(
                nombre=fila[0],
                provincia=fila[1],
                ciudad=fila[2],
                fuente=fila[3]
            )
            servicio = ServicioCanonico(fila[4])
            fecha = date.fromisoformat(fila[7])
            
            ofertas.append(
                Oferta(
                    empresa=empresa,
                    servicio=servicio,
                    precio=fila[5],
                    moneda=fila[6],
                    fecha_relevamiento=fecha
                )
            )
        return ofertas
