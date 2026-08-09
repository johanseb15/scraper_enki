from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import re

from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta


class ClasificacionPrecio(str, Enum):
    NUMERICO_INEQUIVOCO = "numerico_inequivoco"
    NUMERICO_POTENCIALMENTE_AMBIGUO = "numerico_potencialmente_ambiguo"
    SIN_PRECIO = "sin_precio"
    TEXTO_ESPECIAL = "texto_especial"
    INVALIDO = "invalido"


@dataclass(frozen=True)
class PrecioCiroWhite:
    raw: str
    clasificacion: ClasificacionPrecio
    valor_numerico: int | None = None
    precio_minimo: int | None = None
    precio_maximo: int | None = None
    desde: bool = False
    evidencia: str = ""


@dataclass(frozen=True)
class CandidatoCiroWhite:
    categoria_raw: str
    servicio_raw: str
    descripcion_raw: str
    nota_raw: str
    prestaciones_raw: tuple[str, ...]
    precio: PrecioCiroWhite
    empresa_raw: str
    provincia_raw: str
    ciudad_raw: str
    modalidad_raw: str
    url_origen: str
    fecha_relevamiento: date


_CATEGORIAS = {
    "tab-imp": "Impresoras",
    "tab-note": "Notebooks",
    "tab-pc": "PC Escritorio",
}
_NUMERO_CON_MILES = r"\d{1,3}(?:\.\d{3})+"


def _numero_inequivoco(texto: str) -> int | None:
    limpio = texto.strip()
    if re.fullmatch(rf"\$\s*{_NUMERO_CON_MILES}", limpio):
        return int(re.sub(r"\D", "", limpio))
    if re.fullmatch(r"\$\s*\d{4,}", limpio):
        return int(re.sub(r"\D", "", limpio))
    return None


def clasificar_precio_cirowhite(precio_raw: str) -> PrecioCiroWhite:
    raw = " ".join((precio_raw or "").split())
    if not raw:
        return PrecioCiroWhite(
            raw=precio_raw,
            clasificacion=ClasificacionPrecio.SIN_PRECIO,
            evidencia="No existe literal de precio.",
        )

    valor_exacto = _numero_inequivoco(raw)
    if valor_exacto is not None:
        return PrecioCiroWhite(
            raw=precio_raw,
            clasificacion=ClasificacionPrecio.NUMERICO_INEQUIVOCO,
            valor_numerico=valor_exacto,
            evidencia="Literal completo con separador de miles explícito.",
        )

    desde = re.fullmatch(
        rf"Desde\s+(\$\s*{_NUMERO_CON_MILES})(?:\s+.*)?",
        raw,
        re.IGNORECASE,
    )
    if desde:
        valor = _numero_inequivoco(desde.group(1))
        return PrecioCiroWhite(
            raw=precio_raw,
            clasificacion=ClasificacionPrecio.TEXTO_ESPECIAL,
            valor_numerico=valor,
            precio_minimo=valor,
            desde=True,
            evidencia="El número es un límite inferior; no es un precio final exacto.",
        )

    rango = re.fullmatch(
        rf"(\$\s*{_NUMERO_CON_MILES})\s*[–-]\s*(\$\s*{_NUMERO_CON_MILES})",
        raw,
    )
    if rango:
        return PrecioCiroWhite(
            raw=precio_raw,
            clasificacion=ClasificacionPrecio.TEXTO_ESPECIAL,
            precio_minimo=_numero_inequivoco(rango.group(1)),
            precio_maximo=_numero_inequivoco(rango.group(2)),
            evidencia="La fuente publica un rango; no existe un único precio exacto.",
        )

    if re.search(r"consultar|cotizar|presupuesto|a convenir", raw, re.IGNORECASE):
        return PrecioCiroWhite(
            raw=precio_raw,
            clasificacion=ClasificacionPrecio.TEXTO_ESPECIAL,
            evidencia="La fuente exige consulta y no publica un valor numérico.",
        )

    if re.fullmatch(r"\$\s*\d{1,3}", raw) or re.fullmatch(
        r"\$\s*\d{1,3}\s*[–-]\s*\d{1,3}k", raw, re.IGNORECASE
    ):
        return PrecioCiroWhite(
            raw=precio_raw,
            clasificacion=ClasificacionPrecio.NUMERICO_POTENCIALMENTE_AMBIGUO,
            evidencia="El literal no explicita por sí solo si el valor está expresado en miles.",
        )

    return PrecioCiroWhite(
        raw=precio_raw,
        clasificacion=ClasificacionPrecio.INVALIDO,
        evidencia="El literal no coincide con un formato de precio seguro conocido.",
    )


def _texto(nodo) -> str:
    return nodo.get_text(" ", strip=True) if nodo else ""


def extraer_candidatos_cirowhite(
    html: str,
    url_fuente: str,
    fecha_relevamiento: date | None = None,
) -> list[CandidatoCiroWhite]:
    fecha = fecha_relevamiento or date.today()
    soup = BeautifulSoup(html, "html.parser")
    texto_pagina = soup.get_text(" ", strip=True)
    empresa = _texto(soup.select_one(".ft-brand-name")) or "CiroWhite Informática"
    provincia = "Tucumán" if "Tucumán" in texto_pagina else ""
    ciudad = "San Miguel de Tucumán" if "San Miguel de Tucumán" in texto_pagina else ""
    modalidad = "a domicilio" if re.search(r"a domicilio", texto_pagina, re.IGNORECASE) else ""

    candidatos: list[CandidatoCiroWhite] = []
    for tarjeta in soup.select(".services .scard, .scard"):
        servicio = _texto(tarjeta.select_one(".sc-title"))
        if not servicio:
            continue
        descripcion = _texto(tarjeta.select_one(".sc-desc"))
        candidatos.append(
            CandidatoCiroWhite(
                categoria_raw="Servicios",
                servicio_raw=servicio,
                descripcion_raw=descripcion,
                nota_raw=descripcion,
                prestaciones_raw=tuple(
                    _texto(nodo) for nodo in tarjeta.select(".sc-list li")
                ),
                precio=clasificar_precio_cirowhite(
                    _texto(tarjeta.select_one(".sc-price"))
                ),
                empresa_raw=empresa,
                provincia_raw=provincia,
                ciudad_raw=ciudad,
                modalidad_raw=modalidad,
                url_origen=url_fuente,
                fecha_relevamiento=fecha,
            )
        )

    for bloque in soup.select(".tab-content"):
        categoria = _CATEGORIAS.get(bloque.get("id", ""), bloque.get("id", ""))
        for tarjeta in bloque.select(":scope > .pgrid > .pc, :scope > .pc"):
            servicio = _texto(tarjeta.select_one(".pc-name"))
            precio_raw = _texto(tarjeta.select_one(".pc-price"))
            nota = _texto(tarjeta.select_one(".pc-note"))
            prestaciones = tuple(_texto(nodo) for nodo in tarjeta.select(".pc-feats li"))
            if not servicio:
                continue

            candidatos.append(
                CandidatoCiroWhite(
                    categoria_raw=categoria,
                    servicio_raw=servicio,
                    descripcion_raw=nota,
                    nota_raw=nota,
                    prestaciones_raw=prestaciones,
                    precio=clasificar_precio_cirowhite(precio_raw),
                    empresa_raw=empresa,
                    provincia_raw=provincia,
                    ciudad_raw=ciudad,
                    modalidad_raw=modalidad,
                    url_origen=url_fuente,
                    fecha_relevamiento=fecha,
                )
            )

            for prestacion in prestaciones:
                precio_prestacion = re.fullmatch(r"(.+?):\s*(\$\s*[\d.]+)", prestacion)
                if not precio_prestacion:
                    continue
                candidatos.append(
                    CandidatoCiroWhite(
                        categoria_raw=categoria,
                        servicio_raw=precio_prestacion.group(1).strip(),
                        descripcion_raw=prestacion,
                        nota_raw=nota,
                        prestaciones_raw=(),
                        precio=clasificar_precio_cirowhite(precio_prestacion.group(2)),
                        empresa_raw=empresa,
                        provincia_raw=provincia,
                        ciudad_raw=ciudad,
                        modalidad_raw=modalidad,
                        url_origen=url_fuente,
                        fecha_relevamiento=fecha,
                    )
                )

    return candidatos


def parsear_ofertas_cirowhite(
    html: str,
    url_fuente: str,
    fecha_relevamiento: date | None = None,
    rechazos: list[RechazoIngesta] | None = None,
) -> list[OfertaDTO]:
    ofertas: list[OfertaDTO] = []
    for candidato in extraer_candidatos_cirowhite(
        html,
        url_fuente=url_fuente,
        fecha_relevamiento=fecha_relevamiento,
    ):
        if candidato.precio.clasificacion is not ClasificacionPrecio.NUMERICO_INEQUIVOCO:
            if rechazos is not None:
                rechazos.append(
                    RechazoIngesta(
                        fuente=url_fuente,
                        razon=(
                            f"{candidato.servicio_raw}: precio "
                            f"{candidato.precio.clasificacion.value} "
                            f"'{candidato.precio.raw}'"
                        ),
                    )
                )
            continue

        ofertas.append(
            OfertaDTO(
                empresa_nombre=candidato.empresa_raw,
                provincia=candidato.provincia_raw,
                ciudad=candidato.ciudad_raw,
                fuente=url_fuente,
                servicio_raw=candidato.servicio_raw,
                equipo_raw=candidato.categoria_raw,
                precio=candidato.precio.valor_numerico,
                precio_raw=candidato.precio.raw,
                moneda="ARS",
                fecha_relevamiento=candidato.fecha_relevamiento,
            )
        )

    return ofertas
