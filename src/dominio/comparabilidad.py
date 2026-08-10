from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class EstadoComparabilidad(str, Enum):
    POTENCIALMENTE_COMPARABLE = "potencialmente_comparable"
    NO_COMPARABLE = "no_comparable"
    INDETERMINADO = "indeterminado"


class CausaComparabilidad(str, Enum):
    PERIODICIDAD_INCOMPATIBLE = "periodicidad_incompatible"
    PERIODICIDAD_DESCONOCIDA = "periodicidad_desconocida"
    UNIDAD_ECONOMICA_DESCONOCIDA = "unidad_economica_desconocida"
    SCOPE_MATERIAL_DISTINTO = "scope_material_distinto"
    FUENTE_NO_APTA = "fuente_no_apta"
    PRECIO_ORIENTATIVO = "precio_orientativo"


@dataclass(frozen=True)
class ResultadoComparabilidad:
    estado: EstadoComparabilidad
    causas: tuple[CausaComparabilidad, ...] = ()
    advertencias: tuple[CausaComparabilidad, ...] = ()


def evaluar_comparabilidad(
    izquierda,
    derecha,
    *,
    fuentes_no_aptas: Iterable[str] = (),
) -> ResultadoComparabilidad:
    fuentes_no_aptas = set(fuentes_no_aptas)
    if (
        getattr(izquierda.empresa, "fuente", None) in fuentes_no_aptas
        or getattr(derecha.empresa, "fuente", None) in fuentes_no_aptas
    ):
        return ResultadoComparabilidad(
            EstadoComparabilidad.INDETERMINADO,
            (CausaComparabilidad.FUENTE_NO_APTA,),
        )

    periodo_izquierda = _periodo(izquierda)
    periodo_derecha = _periodo(derecha)

    if _scope_material_distinto(izquierda, derecha):
        return ResultadoComparabilidad(
            EstadoComparabilidad.NO_COMPARABLE,
            (CausaComparabilidad.SCOPE_MATERIAL_DISTINTO,),
        )

    if periodo_izquierda != periodo_derecha:
        if periodo_izquierda is None or periodo_derecha is None:
            return ResultadoComparabilidad(
                EstadoComparabilidad.INDETERMINADO,
                (CausaComparabilidad.PERIODICIDAD_DESCONOCIDA,),
            )
        return ResultadoComparabilidad(
            EstadoComparabilidad.NO_COMPARABLE,
            (CausaComparabilidad.PERIODICIDAD_INCOMPATIBLE,),
        )

    if periodo_izquierda not in (None, "puntual"):
        return ResultadoComparabilidad(
            EstadoComparabilidad.INDETERMINADO,
            (CausaComparabilidad.UNIDAD_ECONOMICA_DESCONOCIDA,),
        )

    return ResultadoComparabilidad(
        EstadoComparabilidad.POTENCIALMENTE_COMPARABLE,
        advertencias=_advertencias(izquierda, derecha),
    )


def es_observacion_puntual(oferta) -> bool:
    return getattr(getattr(oferta, "precio", None), "periodo", None) is None


def _periodo(oferta) -> str | None:
    precio = getattr(oferta, "precio", None)
    if hasattr(precio, "periodo"):
        return getattr(precio, "periodo", None) or "puntual"
    return None


def _advertencias(izquierda, derecha) -> tuple[CausaComparabilidad, ...]:
    textos = (
        getattr(izquierda, "precio_raw", None),
        getattr(derecha, "precio_raw", None),
    )
    if any(_contiene_orientativo(texto) for texto in textos):
        return (CausaComparabilidad.PRECIO_ORIENTATIVO,)
    return ()


def _contiene_orientativo(texto: str | None) -> bool:
    if not texto:
        return False
    texto = texto.lower()
    return "orientativo" in texto or "referencia" in texto


def _scope_material_distinto(izquierda, derecha) -> bool:
    scope_izquierda = _scope_material(getattr(izquierda, "servicio_raw", ""))
    scope_derecha = _scope_material(getattr(derecha, "servicio_raw", ""))
    return bool(scope_izquierda.symmetric_difference(scope_derecha))


def _scope_material(texto: str) -> set[str]:
    texto = texto.lower()
    scope = set()
    for palabra in ("equipo", "insumo", "hardware"):
        if palabra in texto:
            scope.add(palabra)
    return scope


