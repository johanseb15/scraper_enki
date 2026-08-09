from datetime import date
from typing import Any, Dict, List

from src.aplicacion.dto.oferta_dto import OfertaDTO


def parsear_ofertas_compragamer(
    data_json: List[Dict[str, Any]], fecha_relevamiento: date
) -> List[OfertaDTO]:
    """Parsea la lista de productos de Compra Gamer a OfertaDTO.

    Soporta los campos nativos: 'nombre', 'precioEspecial' y 'precioLista'.
    """
    dtos: List[OfertaDTO] = []
    vistos = set()

    for item in data_json:
        # Validar que sea un diccionario de producto válido
        if not isinstance(item, dict) or "id_producto" not in item:
            continue

        nombre = item.get("nombre")
        if not nombre or not isinstance(nombre, str):
            continue

        nombre_clean = nombre.strip()
        if nombre_clean in vistos:
            continue

        # Priorizamos precioEspecial (efectivo/transferencia) y luego precioLista
        precio_raw = item.get("precioEspecial") or item.get("precioLista") or 0

        try:
            precio = int(float(precio_raw))
        except (ValueError, TypeError):
            continue

        if precio <= 0:
            continue

        vistos.add(nombre_clean)
        dtos.append(
            OfertaDTO(
                empresa_nombre="Compra Gamer",
                provincia="Buenos Aires",
                ciudad="CABA",
                servicio_raw=nombre_clean,
                precio=precio,
                precio_raw=str(precio_raw),
                moneda="ARS",
                fecha_relevamiento=fecha_relevamiento,
                fuente="compragamer_playwright",
            )
        )

    return dtos
