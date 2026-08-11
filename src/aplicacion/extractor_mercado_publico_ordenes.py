import json
from dataclasses import dataclass, field
from typing import Any

from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import (
    DocumentoRaw,
    RegistroLineaOrdenCompraMercadoPublicoObservada,
    RegistroOrdenCompraMercadoPublicoObservada,
)

UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RechazoLineaMercadoPublico:
    raw_document_id: int | None
    source_record_id: str
    line_index: int
    reason: str


@dataclass(frozen=True)
class RechazoOrdenMercadoPublico:
    raw_document_id: int | None
    source_record_id: str
    reason: str


@dataclass(frozen=True)
class ExtraccionOrdenMercadoPublico:
    order: RegistroOrdenCompraMercadoPublicoObservada
    lines: list[RegistroLineaOrdenCompraMercadoPublicoObservada]
    rejected_lines: list[RechazoLineaMercadoPublico] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoExtraccionMercadoPublico:
    orders_processed: int = 0
    orders_extracted: int = 0
    orders_partial: int = 0
    orders_rejected: int = 0
    duplicate: int = 0
    items_seen: int = 0
    items_extracted: int = 0
    items_partial: int = 0
    items_rejected: int = 0
    rejected_orders: list[RechazoOrdenMercadoPublico] = field(default_factory=list)
    rejected_lines: list[RechazoLineaMercadoPublico] = field(default_factory=list)


class ExtractorMercadoPublicoOrdenes:
    def __init__(self, extractor_version: str = "mercado_publico_purchase_order_v1"):
        self.extractor_version = extractor_version

    def extraer_uno(self, documento: DocumentoRaw) -> ExtraccionOrdenMercadoPublico:
        raw_document_id = self._raw_document_id(documento)
        try:
            raw = json.loads(documento.raw_content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid raw JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError("raw content must be a JSON object")

        codigo = self._pick(raw, "Codigo")
        if codigo == UNKNOWN:
            raise ValueError("missing purchase order Codigo")

        items_container = raw.get("Items") if isinstance(raw.get("Items"), dict) else {}
        listed_items = items_container.get("Listado") if isinstance(items_container, dict) else []
        items = listed_items if isinstance(listed_items, list) else []
        lines: list[RegistroLineaOrdenCompraMercadoPublicoObservada] = []
        rejected_lines: list[RechazoLineaMercadoPublico] = []

        for index, item in enumerate(items):
            try:
                lines.append(self._extraer_linea(documento, raw, str(codigo), index, item))
            except ValueError as exc:
                rejected_lines.append(
                    RechazoLineaMercadoPublico(
                        raw_document_id=raw_document_id,
                        source_record_id=str(codigo),
                        line_index=index,
                        reason=str(exc),
                    )
                )

        status = self._order_status(raw=raw, lines=lines, rejected_lines=rejected_lines)
        order = RegistroOrdenCompraMercadoPublicoObservada(
            raw_document_id=raw_document_id,
            source=documento.source,
            source_record_id=str(codigo),
            source_url=documento.source_url,
            extractor_version=self.extractor_version,
            extraction_status=status,
            rejection_reason="; ".join(line.reason for line in rejected_lines),
            order_code_raw=codigo,
            name_raw=self._pick(raw, "Nombre"),
            description_raw=self._pick(raw, "Descripcion", "Nombre"),
            buyer_raw=self._pick(raw, "Comprador"),
            supplier_raw=self._pick(raw, "Proveedor"),
            status_raw=self._pick(raw, "Estado", "CodigoEstado"),
            date_raw=self._pick(raw, "Fechas"),
            currency_raw=self._pick(raw, "TipoMoneda"),
            order_total_raw=self._pick(raw, "Total"),
            location_raw=self._location_raw(raw),
            items_count_raw=items_container.get("Cantidad", len(items)) if isinstance(items_container, dict) else UNKNOWN,
            metadata={
                "record_type": "PURCHASE_ORDER",
                "raw_items_seen": len(items),
                "valid_lines_extracted": len(lines),
                "line_items_rejected": len(rejected_lines),
                "order_total_semantics": "source_purchase_order_Total",
                "line_total_semantics": "source_item_Total",
                "net_price_semantics": "source_item_PrecioNeto_preserved_not_corrected",
                "sum_line_total_vs_order_total": self._order_total_consistency(raw, lines),
            },
        )
        return ExtraccionOrdenMercadoPublico(order=order, lines=lines, rejected_lines=rejected_lines)

    def extraer_lote(
        self,
        documentos: list[DocumentoRaw],
        repositorio: RepositorioEvidencia,
    ) -> ResultadoExtraccionMercadoPublico:
        orders_extracted = 0
        orders_partial = 0
        duplicate = 0
        items_seen = 0
        items_extracted = 0
        items_partial = 0
        rejected_orders: list[RechazoOrdenMercadoPublico] = []
        rejected_lines: list[RechazoLineaMercadoPublico] = []

        for documento in documentos:
            try:
                extraccion = self.extraer_uno(documento)
            except ValueError as exc:
                rejected_orders.append(
                    RechazoOrdenMercadoPublico(
                        raw_document_id=documento.storage_id,
                        source_record_id=documento.source_record_id,
                        reason=str(exc),
                    )
                )
                continue

            items_seen += extraccion.order.metadata["raw_items_seen"]
            rejected_lines.extend(extraccion.rejected_lines)
            saved = repositorio.guardar_observacion_mercado_publico_orden_con_lineas(
                extraccion.order, extraccion.lines
            )
            if not saved:
                duplicate += 1
                continue
            if extraccion.order.extraction_status == "PARTIAL":
                orders_partial += 1
            else:
                orders_extracted += 1
            items_extracted += len(extraccion.lines)
            items_partial += sum(1 for line in extraccion.lines if line.extraction_status == "PARTIAL")

        return ResultadoExtraccionMercadoPublico(
            orders_processed=len(documentos),
            orders_extracted=orders_extracted,
            orders_partial=orders_partial,
            orders_rejected=len(rejected_orders),
            duplicate=duplicate,
            items_seen=items_seen,
            items_extracted=items_extracted,
            items_partial=items_partial,
            items_rejected=len(rejected_lines),
            rejected_orders=rejected_orders,
            rejected_lines=rejected_lines,
        )

    def _extraer_linea(
        self,
        documento: DocumentoRaw,
        raw_order: dict[str, Any],
        codigo_orden: str,
        index: int,
        item: Any,
    ) -> RegistroLineaOrdenCompraMercadoPublicoObservada:
        if not isinstance(item, dict):
            raise ValueError("item must be a JSON object")
        if not item:
            raise ValueError("empty item")

        description_raw = self._pick(item, "EspecificacionComprador", "Producto", "Descripcion")
        category_raw = self._pick(item, "Categoria")
        quantity_raw = self._pick(item, "Cantidad")
        unit_raw = self._pick(item, "Unidad")
        net_price_raw = self._pick(item, "PrecioNeto")
        total_raw = self._pick(item, "Total")
        currency_raw = self._pick(item, "Moneda", fallback=self._pick(raw_order, "TipoMoneda"))
        category_code_raw = self._pick(item, "CodigoCategoria")
        product_code_raw = self._pick(item, "CodigoProducto")
        if all(value == UNKNOWN for value in [description_raw, category_raw, quantity_raw, net_price_raw, total_raw]):
            raise ValueError("item without observable description/category/economics")

        status = "PARTIAL" if description_raw == UNKNOWN or quantity_raw == UNKNOWN or net_price_raw == UNKNOWN or total_raw == UNKNOWN else "EXTRACTED"
        item_stable_id_raw = self._item_stable_id(item, index)
        return RegistroLineaOrdenCompraMercadoPublicoObservada(
            raw_document_id=self._raw_document_id(documento),
            source=documento.source,
            source_record_id=f"{codigo_orden}:LINE:{index}",
            source_url=documento.source_url,
            extractor_version=self.extractor_version,
            extraction_status=status,
            rejection_reason="" if status == "EXTRACTED" else "missing core line fields",
            order_source_record_id=codigo_orden,
            order_observation_id=None,
            line_index=index,
            item_stable_id_raw=item_stable_id_raw,
            description_raw=description_raw,
            category_raw=category_raw,
            category_code_raw=category_code_raw,
            product_code_raw=product_code_raw,
            quantity_raw=quantity_raw,
            unit_raw=unit_raw,
            net_price_raw=net_price_raw,
            total_raw=total_raw,
            currency_raw=currency_raw,
            metadata={
                "raw_item": item,
                "economic_semantics": {
                    "quantity": "source_item_quantity",
                    "unit": "source_item_unit_or_UNKNOWN",
                    "net_price": "source_item_PrecioNeto",
                    "item_total": "source_item_Total",
                },
                "quantity_times_net_price_vs_line_total": self._line_total_consistency(quantity_raw, net_price_raw, total_raw),
            },
        )

    @staticmethod
    def _raw_document_id(documento: DocumentoRaw) -> int:
        if documento.storage_id is None:
            raise ValueError("missing raw document storage id")
        return documento.storage_id

    @staticmethod
    def _pick(raw: dict[str, Any], *keys: str, fallback: Any = UNKNOWN) -> Any:
        for key in keys:
            value = raw.get(key)
            if value not in (None, "", [], {}):
                return value
        return fallback

    @classmethod
    def _location_raw(cls, raw: dict[str, Any]) -> dict[str, Any]:
        comprador = raw.get("Comprador") if isinstance(raw.get("Comprador"), dict) else {}
        proveedor = raw.get("Proveedor") if isinstance(raw.get("Proveedor"), dict) else {}
        return {
            "pais_raw": cls._pick(raw, "Pais"),
            "buyer_region_raw": cls._pick(comprador, "RegionUnidad"),
            "buyer_comuna_raw": cls._pick(comprador, "ComunaUnidad"),
            "supplier_region_raw": cls._pick(proveedor, "Region"),
            "supplier_comuna_raw": cls._pick(proveedor, "Comuna"),
        }

    @staticmethod
    def _item_stable_id(item: dict[str, Any], index: int) -> Any:
        for key in ["Correlativo", "Codigo", "Id", "CodigoProducto"]:
            value = item.get(key)
            if value not in (None, "", [], {}):
                return value
        return f"INDEX:{index}"

    @staticmethod
    def _line_total_consistency(quantity: Any, net_price: Any, total: Any) -> str:
        if UNKNOWN in (quantity, net_price, total):
            return "NOT_EVALUABLE"
        try:
            expected = float(quantity) * float(net_price)
            observed = float(total)
        except (TypeError, ValueError):
            return "NOT_EVALUABLE"
        return "MATCH" if abs(expected - observed) < 0.01 else "MISMATCH"

    @classmethod
    def _order_total_consistency(
        cls,
        raw: dict[str, Any],
        lines: list[RegistroLineaOrdenCompraMercadoPublicoObservada],
    ) -> str:
        order_total = cls._pick(raw, "Total")
        if order_total == UNKNOWN or not lines:
            return "NOT_EVALUABLE"
        total = 0.0
        for line in lines:
            if line.total_raw == UNKNOWN:
                return "NOT_EVALUABLE"
            try:
                total += float(line.total_raw)
            except (TypeError, ValueError):
                return "NOT_EVALUABLE"
        try:
            observed = float(order_total)
        except (TypeError, ValueError):
            return "NOT_EVALUABLE"
        return "MATCH" if abs(total - observed) < 0.01 else "MISMATCH"

    @classmethod
    def _order_status(
        cls,
        *,
        raw: dict[str, Any],
        lines: list[RegistroLineaOrdenCompraMercadoPublicoObservada],
        rejected_lines: list[RechazoLineaMercadoPublico],
    ) -> str:
        core = [
            cls._pick(raw, "Codigo"),
            cls._pick(raw, "Comprador"),
            cls._pick(raw, "Proveedor"),
            cls._pick(raw, "TipoMoneda"),
            cls._pick(raw, "Total"),
        ]
        if rejected_lines or not lines or any(value == UNKNOWN for value in core):
            return "PARTIAL"
        return "EXTRACTED"
