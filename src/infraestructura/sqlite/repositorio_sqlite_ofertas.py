import sqlite3
from datetime import date

from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta, PrecioValor
from src.dominio.servicios import ServicioCanonico


class RepositorioSQLiteOfertas:
    """Persistencia SQLite de la entidad oficial Oferta."""

    _COLUMNAS_TRAZABLES = {
        "ciudad": "TEXT",
        "fecha_relevamiento": "TEXT",
        "servicio_raw": "TEXT",
        "modalidad": "TEXT",
        "precio_raw": "TEXT",
    }

    def __init__(self, *args, **kwargs):
        ruta_db = args[0] if args else self._obtener_ruta(kwargs)
        self.ruta_db = ruta_db
        self.conexion = sqlite3.connect(ruta_db)
        self.conexion.row_factory = sqlite3.Row
        self._crear_o_migrar_tabla()

    @staticmethod
    def _obtener_ruta(kwargs) -> str:
        for nombre in ("ruta_db", "db_path", "path", "database"):
            if nombre in kwargs:
                return kwargs[nombre]
        return "datos.db"

    def _crear_o_migrar_tabla(self) -> None:
        with self.conexion:
            self.conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS ofertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT,
                    fuente TEXT,
                    servicio TEXT,
                    precio REAL,
                    moneda TEXT,
                    provincia TEXT,
                    ciudad TEXT,
                    fecha_relevamiento TEXT,
                    servicio_raw TEXT,
                    modalidad TEXT,
                    precio_raw TEXT
                )
                """
            )
            columnas = {
                fila["name"]
                for fila in self.conexion.execute("PRAGMA table_info(ofertas)")
            }
            for nombre, tipo in self._COLUMNAS_TRAZABLES.items():
                if nombre not in columnas:
                    self.conexion.execute(
                        f"ALTER TABLE ofertas ADD COLUMN {nombre} {tipo}"
                    )
            if "fecha" in columnas:
                self.conexion.execute(
                    """
                    UPDATE ofertas
                    SET fecha_relevamiento = fecha
                    WHERE fecha_relevamiento IS NULL AND fecha IS NOT NULL
                    """
                )

    def guardar(self, oferta: Oferta) -> Oferta:
        servicio = (
            oferta.servicio.value
            if isinstance(oferta.servicio, ServicioCanonico)
            else oferta.servicio
        )
        precio = (
            oferta.precio.valor
            if hasattr(oferta.precio, "valor")
            else oferta.precio
        )
        fecha_relevamiento = (
            oferta.fecha_relevamiento.isoformat()
            if oferta.fecha_relevamiento is not None
            else None
        )

        with self.conexion:
            self.conexion.execute(
                """
                INSERT INTO ofertas (
                    empresa,
                    fuente,
                    servicio,
                    precio,
                    moneda,
                    provincia,
                    ciudad,
                    fecha_relevamiento,
                    servicio_raw,
                    modalidad,
                    precio_raw
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    oferta.empresa.nombre,
                    oferta.empresa.fuente,
                    servicio,
                    precio,
                    oferta.moneda,
                    oferta.empresa.provincia,
                    oferta.empresa.ciudad,
                    fecha_relevamiento,
                    oferta.servicio_raw,
                    oferta.modalidad,
                    oferta.precio_raw,
                ),
            )
        return oferta

    def obtener_todas(self) -> list[Oferta]:
        filas = self.conexion.execute("SELECT * FROM ofertas").fetchall()
        return [self._reconstruir_oferta(fila) for fila in filas]

    @staticmethod
    def _reconstruir_servicio(valor: str) -> ServicioCanonico:
        try:
            return ServicioCanonico(valor)
        except ValueError:
            return ServicioCanonico[valor]

    @classmethod
    def _reconstruir_oferta(cls, fila: sqlite3.Row) -> Oferta:
        empresa = Empresa(
            nombre=fila["empresa"],
            provincia=fila["provincia"],
            ciudad=fila["ciudad"],
            fuente=fila["fuente"],
        )
        precio = (
            PrecioValor(fila["precio"], fila["moneda"])
            if fila["precio"] is not None
            else None
        )
        fecha_relevamiento = (
            date.fromisoformat(fila["fecha_relevamiento"])
            if fila["fecha_relevamiento"]
            else None
        )

        return Oferta(
            empresa=empresa,
            servicio=cls._reconstruir_servicio(fila["servicio"]),
            precio=precio,
            moneda=fila["moneda"],
            fecha_relevamiento=fecha_relevamiento,
            servicio_raw=fila["servicio_raw"],
            modalidad=fila["modalidad"],
            precio_raw=fila["precio_raw"],
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar()

    def cerrar(self) -> None:
        self.conexion.close()
