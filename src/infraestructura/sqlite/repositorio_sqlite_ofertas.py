import sqlite3
from contextlib import closing
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
        "periodo": "TEXT",
    }
    _COLUMNAS_IDENTIDAD = {
        "empresa",
        "fuente",
        "servicio",
        "precio",
        "moneda",
        "provincia",
        "ciudad",
        "fecha_relevamiento",
        "servicio_raw",
        "modalidad",
        "precio_raw",
        "periodo",
    }

    def __init__(self, *args, **kwargs):
        ruta_db = args[0] if args else self._obtener_ruta(kwargs)
        self.ruta_db = ruta_db
        self._crear_o_migrar_tabla()

    @staticmethod
    def _obtener_ruta(kwargs) -> str:
        for nombre in ("ruta_db", "db_path", "path", "database"):
            if nombre in kwargs:
                return kwargs[nombre]
        return "datos.db"

    def _conectar(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.ruta_db)
        conexion.row_factory = sqlite3.Row
        return conexion

    def _crear_o_migrar_tabla(self) -> None:
        with closing(self._conectar()) as conexion, conexion:
            conexion.execute(
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
                    precio_raw TEXT,
                    periodo TEXT
                )
                """
            )
            columnas = {
                fila["name"]
                for fila in conexion.execute("PRAGMA table_info(ofertas)")
            }
            for nombre, tipo in self._COLUMNAS_TRAZABLES.items():
                if nombre not in columnas:
                    conexion.execute(
                        f"ALTER TABLE ofertas ADD COLUMN {nombre} {tipo}"
                    )
            if "fecha" in columnas:
                conexion.execute(
                    """
                    UPDATE ofertas
                    SET fecha_relevamiento = fecha
                    WHERE fecha_relevamiento IS NULL AND fecha IS NOT NULL
                    """
                )
            columnas = {
                fila["name"]
                for fila in conexion.execute("PRAGMA table_info(ofertas)")
            }
            if self._COLUMNAS_IDENTIDAD.issubset(columnas):
                conexion.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                        idx_ofertas_observacion_unica
                    ON ofertas (
                        COALESCE(empresa, X'00'),
                        COALESCE(fuente, X'00'),
                        COALESCE(provincia, X'00'),
                        COALESCE(ciudad, X'00'),
                        COALESCE(
                            NULLIF(servicio_raw, ''),
                            servicio,
                            X'00'
                        ),
                        COALESCE(
                            NULLIF(precio_raw, ''),
                            precio,
                            X'00'
                        ),
                        COALESCE(moneda, X'00'),
                        COALESCE(periodo, X'00'),
                        COALESCE(fecha_relevamiento, X'00'),
                        COALESCE(modalidad, X'00')
                    )
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

        with closing(self._conectar()) as conexion, conexion:
            conexion.execute(
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
                    precio_raw,
                    periodo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
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
                    getattr(oferta.precio, "periodo", None),
                ),
            )
        return oferta

    def obtener_todas(self) -> list[Oferta]:
        with closing(self._conectar()) as conexion:
            filas = conexion.execute("SELECT * FROM ofertas").fetchall()
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
            PrecioValor(fila["precio"], fila["moneda"], fila["periodo"])
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
        pass
