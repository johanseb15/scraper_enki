import json
from datetime import datetime, timezone

from src.aplicacion.extractor_mercado_publico_ordenes import (
    ExtractorMercadoPublicoOrdenes,
    UNKNOWN,
)
from src.dominio.evidencia import DocumentoRaw
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


def _documento(raw, storage_id=1):
    return DocumentoRaw(
        source="mercado_publico_cl",
        source_record_id=f"PURCHASE_ORDER:{raw.get('Codigo', 'UNKNOWN')}",
        source_url="https://api.mercadopublico.cl/servicios/v1/publico/ordenesdecompra.json?codigo=100",
        retrieved_at=datetime(2026, 8, 10, 18, 0, tzinfo=timezone.utc),
        content_type="application/json",
        raw_content=json.dumps(raw, ensure_ascii=False, sort_keys=True),
        content_hash="hash-1",
        metadata={"record_type": "PURCHASE_ORDER"},
        storage_id=storage_id,
    )


def _orden(codigo="100", items=None):
    return {
        "Codigo": codigo,
        "Nombre": "Servicio cloud Microsoft Azure",
        "Descripcion": "Servicio cloud Microsoft Azure por 36 meses",
        "Estado": "Recepci?n Conforme",
        "TipoMoneda": "CLP",
        "Total": 419832000.0,
        "Pais": "CL",
        "Fechas": {"FechaCreacion": "2026-02-26T12:38:01.707"},
        "Comprador": {"NombreOrganismo": "DIRECCION DE EDUCACION PUBLICA", "RegionUnidad": "Metropolitana"},
        "Proveedor": {"Codigo": "1437228", "Nombre": "Andestic SpA", "Comuna": "Santiago"},
        "Items": {"Cantidad": len(items or []), "Listado": items if items is not None else [_item(), _item(producto="Soporte", cantidad=12.0, precio=1000.0, total=12000.0)]},
    }


def _item(producto="Almacenamiento de datos", cantidad=1.0, unidad=None, precio=352800000.0, total=352800000.0):
    return {
        "CodigoCategoria": 81111800,
        "Categoria": "Servicios inform?ticos / Administraci?n de sistemas",
        "CodigoProducto": 81111807,
        "Producto": producto,
        "EspecificacionComprador": producto,
        "Cantidad": cantidad,
        "Unidad": unidad,
        "Moneda": "CLP",
        "PrecioNeto": precio,
        "Total": total,
    }


def test_extrae_una_orden_y_n_lineas_sin_colapsar_items(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    resultado = ExtractorMercadoPublicoOrdenes().extraer_lote([_documento(_orden())], repo)

    assert resultado.orders_processed == 1
    assert resultado.orders_extracted == 1
    assert resultado.items_seen == 2
    assert resultado.items_extracted == 2
    ordenes = repo.listar_observaciones_mercado_publico_ordenes()
    lineas = repo.listar_observaciones_mercado_publico_lineas()
    assert len(ordenes) == 1
    assert len(lineas) == 2
    assert lineas[0].raw_document_id == ordenes[0].raw_document_id
    assert lineas[0].order_observation_id == ordenes[0].storage_id
    assert lineas[0].line_index == 0


def test_item_con_unit_null_es_linea_valida_con_unknown():
    extraccion = ExtractorMercadoPublicoOrdenes().extraer_uno(_documento(_orden(items=[_item(unidad=None)])))

    assert extraccion.order.extraction_status == "EXTRACTED"
    assert extraccion.lines[0].unit_raw == UNKNOWN


def test_preserva_quantity_precio_neto_y_total_sin_convertir_a_oferta():
    extraccion = ExtractorMercadoPublicoOrdenes().extraer_uno(
        _documento(_orden(items=[_item(cantidad=3.0, precio=2500.0, total=7500.0)]))
    )

    linea = extraccion.lines[0]
    assert linea.quantity_raw == 3.0
    assert linea.net_price_raw == 2500.0
    assert linea.total_raw == 7500.0
    assert linea.metadata["economic_semantics"] == {
        "quantity": "source_item_quantity",
        "unit": "source_item_unit_or_UNKNOWN",
        "net_price": "source_item_PrecioNeto",
        "item_total": "source_item_Total",
    }
    assert "oferta" not in linea.metadata


def test_reextraer_mismo_raw_y_version_no_duplica_orden_ni_lineas(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    extractor = ExtractorMercadoPublicoOrdenes("mercado_publico_purchase_order_v1")
    doc = _documento(_orden())

    extractor.extraer_lote([doc], repo)
    resultado = extractor.extraer_lote([doc], repo)

    assert resultado.orders_extracted == 0
    assert resultado.duplicate == 1
    assert repo.contar_observaciones_mercado_publico_ordenes() == 1
    assert repo.contar_observaciones_mercado_publico_lineas() == 2


def test_item_malformado_no_destruye_orden_y_batch_continua(tmp_path):
    repo = RepositorioSQLiteEvidencia(str(tmp_path / "evidence.db"))
    raw = _orden(items=[_item(), {}])
    valid = _orden("101", items=[_item(producto="Cable HDMI")])

    resultado = ExtractorMercadoPublicoOrdenes().extraer_lote([_documento(raw, 1), _documento(valid, 2)], repo)

    assert resultado.orders_processed == 2
    assert resultado.orders_extracted == 1
    assert resultado.orders_partial == 1
    assert resultado.items_seen == 3
    assert resultado.items_extracted == 2
    assert resultado.items_rejected == 1
    assert repo.contar_observaciones_mercado_publico_ordenes() == 2
    assert repo.contar_observaciones_mercado_publico_lineas() == 2
