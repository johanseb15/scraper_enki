from typing import Any, Iterable

from src.dominio.comparabilidad import es_observacion_puntual
from src.dominio.servicios import ServicioCanonico


def _extraer_monto(item: Any) -> float | None:
    if item is None:
        return None
    if isinstance(item, (int, float)):
        return float(item)
    if hasattr(item, "precio"):
        precio_val = item.precio
        if hasattr(precio_val, "monto"):
            return float(precio_val.monto)
        if isinstance(precio_val, (int, float)):
            return float(precio_val)
    if hasattr(item, "monto"):
        return float(item.monto)
    return None


def _precios_puntuales_representables(ofertas: Iterable[Any]) -> list[float]:
    return [
        precio
        for oferta in ofertas
        if es_observacion_puntual(oferta)
        and (precio := _extraer_monto(oferta)) is not None
        and precio > 0
    ]


def calcular_precio_promedio(ofertas: Iterable[Any]) -> float:
    precios = _precios_puntuales_representables(ofertas)
    if not precios:
        return 0.0
    return sum(precios) / len(precios)


def calcular_precio_minimo(ofertas: Iterable[Any]) -> float:
    precios = _precios_puntuales_representables(ofertas)
    if not precios:
        return 0.0
    return min(precios)


def calcular_precio_maximo(ofertas: Iterable[Any]) -> float:
    precios = _precios_puntuales_representables(ofertas)
    if not precios:
        return 0.0
    return max(precios)


def calcular_promedio_por_servicio(
    ofertas: Iterable[Any], servicio: ServicioCanonico
) -> float:
    ofertas_filtradas = [o for o in ofertas if getattr(o, "servicio", None) == servicio]
    return calcular_precio_promedio(ofertas_filtradas)


class CalculadorEstadisticas:

    @staticmethod
    def calcular_promedio_por_servicio(
        ofertas: list[Any], servicio: ServicioCanonico
    ) -> float:
        return calcular_promedio_por_servicio(ofertas, servicio)
