import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import DocumentoRaw, FuenteCandidata


class ClienteMercadoPublico(Protocol):
    def listar_ordenes(self, *, fecha: str, estado: str, limit: int) -> list[dict[str, Any]]:
        """Devuelve registros basicos de ordenes de compra."""

    def obtener_orden(self, codigo: str) -> dict[str, Any]:
        """Devuelve detalle oficial de una orden de compra."""


@dataclass(frozen=True)
class RegistroMercadoPublicoRechazado:
    index: int
    source_record_id: str
    reason: str


@dataclass(frozen=True)
class ResultadoMercadoPublico:
    requested: int = 0
    downloaded: int = 0
    accepted: int = 0
    duplicate: int = 0
    rejected: int = 0
    failed: int = 0
    not_available: int = 0
    rejected_records: list[RegistroMercadoPublicoRechazado] = field(default_factory=list)


class ColectorMercadoPublicoCL:
    def __init__(
        self,
        cliente: ClienteMercadoPublico,
        repositorio: RepositorioEvidencia,
        reloj: Callable[[], datetime] | None = None,
    ):
        self.cliente = cliente
        self.repositorio = repositorio
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))

    def colectar_ordenes(
        self, *, fecha: str, limit: int, estado: str = "todos"
    ) -> ResultadoMercadoPublico:
        try:
            basicas = self.cliente.listar_ordenes(fecha=fecha, estado=estado, limit=limit)
        except Exception:
            return ResultadoMercadoPublico(requested=limit, failed=1)

        accepted = 0
        duplicate = 0
        rejected = 0
        failed = 0
        not_available = 0
        rejected_records: list[RegistroMercadoPublicoRechazado] = []
        for index, basica in enumerate(basicas, start=1):
            codigo = str(basica.get("Codigo") or "").strip()
            if not codigo:
                rejected += 1
                rejected_records.append(
                    RegistroMercadoPublicoRechazado(index, "UNKNOWN", "missing Codigo")
                )
                continue
            try:
                detalle = self.cliente.obtener_orden(codigo)
            except LookupError as exc:
                not_available += 1
                rejected_records.append(
                    RegistroMercadoPublicoRechazado(index, codigo, str(exc))
                )
                continue
            except Exception as exc:
                failed += 1
                rejected_records.append(
                    RegistroMercadoPublicoRechazado(index, codigo, str(exc))
                )
                continue
            try:
                documento = self._crear_documento(detalle, fecha=fecha, estado=estado)
            except ValueError as exc:
                rejected += 1
                rejected_records.append(
                    RegistroMercadoPublicoRechazado(index, codigo, str(exc))
                )
                continue
            if self.repositorio.guardar_documento_raw(documento):
                accepted += 1
            else:
                duplicate += 1

        if accepted or duplicate:
            self._registrar_fuente_activa()

        return ResultadoMercadoPublico(
            requested=limit,
            downloaded=len(basicas),
            accepted=accepted,
            duplicate=duplicate,
            rejected=rejected,
            failed=failed,
            not_available=not_available,
            rejected_records=rejected_records,
        )

    def _crear_documento(
        self, detalle: dict[str, Any], *, fecha: str, estado: str
    ) -> DocumentoRaw:
        codigo = str(detalle.get("Codigo") or "").strip()
        if not codigo:
            raise ValueError("missing Codigo")
        raw_content = json.dumps(detalle, ensure_ascii=False, sort_keys=True)
        content_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        items = self._items(detalle)
        return DocumentoRaw(
            source="mercado_publico_cl",
            source_record_id=f"PURCHASE_ORDER:{codigo}",
            source_url=(
                "https://api.mercadopublico.cl/servicios/v1/publico/"
                f"ordenesdecompra.json?codigo={codigo}"
            ),
            retrieved_at=self.reloj(),
            content_type="application/json",
            raw_content=raw_content,
            content_hash=content_hash,
            metadata={
                "record_type": "PURCHASE_ORDER",
                "query": {"fecha": fecha, "estado": estado},
                "buyer_raw": detalle.get("Comprador", "UNKNOWN"),
                "supplier_raw": detalle.get("Proveedor", "UNKNOWN"),
                "description_raw": detalle.get("Descripcion", "UNKNOWN"),
                "status_raw": detalle.get("Estado", detalle.get("CodigoEstado", "UNKNOWN")),
                "currency_raw": detalle.get("TipoMoneda", "UNKNOWN"),
                "total_amount_raw": detalle.get("Total", "UNKNOWN"),
                "net_amount_raw": detalle.get("TotalNeto", "UNKNOWN"),
                "date_raw": detalle.get("Fechas", "UNKNOWN"),
                "location_raw": {
                    "buyer_country": (detalle.get("Comprador") or {}).get("Pais", "UNKNOWN") if isinstance(detalle.get("Comprador"), dict) else "UNKNOWN",
                    "supplier_country": (detalle.get("Proveedor") or {}).get("Pais", "UNKNOWN") if isinstance(detalle.get("Proveedor"), dict) else "UNKNOWN",
                    "country": detalle.get("Pais", "UNKNOWN"),
                },
                "items_count": len(items),
                "items_raw": items,
                "records_with_multiple_items": len(items) > 1,
                "quantity_fields_present": sum(1 for item in items if item.get("Cantidad") not in (None, "", [], {})),
                "unit_fields_present": sum(1 for item in items if item.get("Unidad") not in (None, "", [], {})),
                "unit_price_fields_present": sum(1 for item in items if item.get("PrecioNeto") not in (None, "", [], {})),
                "category_raw": [
                    {
                        "CodigoCategoria": item.get("CodigoCategoria", "UNKNOWN"),
                        "Categoria": item.get("Categoria", "UNKNOWN"),
                        "CodigoProducto": item.get("CodigoProducto", "UNKNOWN"),
                        "Producto": item.get("Producto", "UNKNOWN"),
                    }
                    for item in items
                ],
                "value_semantics": "purchase_order_total",
                "line_item_semantics": "explicit_source_line_items",
            },
        )

    @staticmethod
    def _items(detalle: dict[str, Any]) -> list[dict[str, Any]]:
        items = detalle.get("Items")
        if not isinstance(items, dict):
            return []
        listado = items.get("Listado")
        if not isinstance(listado, list):
            return []
        return [item for item in listado if isinstance(item, dict)]

    def _registrar_fuente_activa(self) -> None:
        self.repositorio.guardar_fuente(
            FuenteCandidata(
                name="Mercado Público ChileCompra API",
                url="https://api.mercadopublico.cl/servicios/v1/publico/",
                source_type="public_procurement_api",
                country="CL",
                language="es",
                acquisition_method="official_api",
                status="ACTIVE",
                last_checked_at=self.reloj(),
                notes="Ordenes de compra detalladas con items desde API oficial",
                metadata={"source": "mercado_publico_cl"},
            )
        )
