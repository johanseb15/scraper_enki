from datetime import datetime, timezone

from src.aplicacion.colector_mercado_publico import ColectorMercadoPublicoCL
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


class ClienteMercadoFake:
    def __init__(self, detalles):
        self.detalles = detalles

    def listar_ordenes(self, *, fecha: str, estado: str, limit: int):
        return [{"Codigo": codigo, "Nombre": "Orden", "CodigoEstado": 6} for codigo in self.detalles][:limit]

    def obtener_orden(self, codigo: str):
        value = self.detalles[codigo]
        if isinstance(value, Exception):
            raise value
        return value


def _orden(codigo="1002584-75-SE26", total=419832000.0):
    return {
        "Codigo": codigo,
        "Nombre": "Servicio cloud Microsoft Azure",
        "Estado": "Recepción Conforme",
        "TipoMoneda": "CLP",
        "Total": total,
        "Fechas": {"FechaCreacion": "2026-02-26T12:38:01.707"},
        "Comprador": {"NombreOrganismo": "DIRECCION DE EDUCACION PUBLICA"},
        "Proveedor": {"Codigo": "1437228", "Nombre": "Andestic SpA"},
        "Items": {
            "Cantidad": 2,
            "Listado": [
                {
                    "CodigoCategoria": 81111800,
                    "Categoria": "Servicios informáticos / Administración de sistemas",
                    "Producto": "Almacenamiento de datos",
                    "Cantidad": 1.0,
                    "Unidad": None,
                    "Moneda": "CLP",
                    "PrecioNeto": 352800000.0,
                    "Total": 352800000.0,
                },
                {
                    "CodigoCategoria": 81111800,
                    "Producto": "Soporte",
                    "Cantidad": 12.0,
                    "Unidad": "Mes",
                    "Moneda": "CLP",
                    "PrecioNeto": 1000.0,
                    "Total": 12000.0,
                },
            ],
        },
    }


def test_mercado_publico_real_shaped_order_crea_documento_raw_y_preserva_items(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))

    resultado = ColectorMercadoPublicoCL(
        cliente=ClienteMercadoFake({"1002584-75-SE26": _orden()}),
        repositorio=repo,
        reloj=lambda: datetime(2026, 8, 10, 17, 0, tzinfo=timezone.utc),
    ).colectar_ordenes(fecha="10082026", limit=1)

    assert resultado.accepted == 1
    docs = repo.listar_documentos_raw(source="mercado_publico_cl")
    assert len(docs) == 1
    assert docs[0].source_record_id == "PURCHASE_ORDER:1002584-75-SE26"
    assert docs[0].metadata["record_type"] == "PURCHASE_ORDER"
    assert docs[0].metadata["items_count"] == 2
    assert docs[0].metadata["value_semantics"] == "purchase_order_total"


def test_mercado_publico_repetido_no_duplica(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    collector = ColectorMercadoPublicoCL(ClienteMercadoFake({"100": _orden("100")}), repo)

    collector.colectar_ordenes(fecha="10082026", limit=1)
    resultado = collector.colectar_ordenes(fecha="10082026", limit=1)

    assert resultado.accepted == 0
    assert resultado.duplicate == 1
    assert repo.contar_documentos_raw(source="mercado_publico_cl") == 1


def test_mercado_publico_malformed_rejected_batch_continues(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))

    resultado = ColectorMercadoPublicoCL(
        ClienteMercadoFake({"bad": {"Nombre": "sin codigo"}, "ok": _orden("ok")}), repo
    ).colectar_ordenes(fecha="10082026", limit=2)

    assert resultado.downloaded == 2
    assert resultado.accepted == 1
    assert resultado.rejected == 1
    assert repo.contar_documentos_raw(source="mercado_publico_cl") == 1


def test_mercado_publico_mismo_id_con_raw_distinto_preserva_revision(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    first = ColectorMercadoPublicoCL(ClienteMercadoFake({"100": _orden("100", 10)}), repo)
    second = ColectorMercadoPublicoCL(ClienteMercadoFake({"100": _orden("100", 20)}), repo)

    first.colectar_ordenes(fecha="10082026", limit=1)
    resultado = second.colectar_ordenes(fecha="10082026", limit=1)

    assert resultado.accepted == 1
    assert repo.contar_documentos_raw(source="mercado_publico_cl") == 2


def test_mercado_publico_multiple_items_no_colapsa_precio_unitario(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))

    ColectorMercadoPublicoCL(
        ClienteMercadoFake({"1002584-75-SE26": _orden()}), repo
    ).colectar_ordenes(fecha="10082026", limit=1)

    doc = repo.listar_documentos_raw(source="mercado_publico_cl")[0]
    assert doc.metadata["items_count"] == 2
    assert doc.metadata["unit_price_fields_present"] == 2
