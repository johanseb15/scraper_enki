from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import re

from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.normalizadores.normalizador_precios import NormalizadorPrecios


class SemanticaPrecioReed(str, Enum):
    EXACTO = "exacto"
    CERO = "cero"
    DESDE = "desde"
    RANGO = "rango"
    CONSULTAR = "consultar"
    AUSENCIA = "ausencia"
    AMBIGUO = "ambiguo"
    OTRO = "otro"


@dataclass(frozen=True)
class PrecioReed:
    raw: str
    semantica: SemanticaPrecioReed
    valor_interpretado: int | None
    evidencia: str


@dataclass(frozen=True)
class ContextoReed:
    empresa_raw: str
    provincia_raw: str
    ciudad_raw: str
    categoria_raw: str
    producto_raw: str
    sku_raw: str
    precio_producto_raw: str
    precio_producto_semantica: SemanticaPrecioReed
    moneda_raw: str
    availability_raw: str
    iva_incluido_raw: str
    url_origen: str
    vigencia_raw: str


@dataclass(frozen=True)
class CandidatoReed:
    tipo_candidato: str
    categoria_raw: str
    producto_raw: str
    servicio_raw: str
    descripcion_raw: str
    precio: PrecioReed
    moneda: str
    empresa_raw: str
    provincia_raw: str
    ciudad_raw: str
    modalidad_raw: str
    url_origen: str
    fecha_relevamiento: date


_PATRON_PRECIO = re.compile(r"\$\s*\d+(?:[.,]\d+)*")


def _texto(nodo) -> str:
    return " ".join(nodo.get_text(" ", strip=True).split()) if nodo else ""


def clasificar_precio_reed(precio_raw: str | None) -> PrecioReed:
    raw_original = "" if precio_raw is None else str(precio_raw)
    raw = " ".join(raw_original.split())
    if not raw:
        return PrecioReed(
            raw=raw_original,
            semantica=SemanticaPrecioReed.AUSENCIA,
            valor_interpretado=None,
            evidencia="La fuente no publica un literal de precio.",
        )

    if re.search(r"\bdesde\b", raw, re.IGNORECASE):
        return PrecioReed(
            raw=raw_original,
            semantica=SemanticaPrecioReed.DESDE,
            valor_interpretado=None,
            evidencia="El literal expresa un limite inferior, no un precio exacto.",
        )

    if re.search(r"\$\s*\d[\d.]*\s*[-–]\s*\$?\s*\d", raw):
        return PrecioReed(
            raw=raw_original,
            semantica=SemanticaPrecioReed.RANGO,
            valor_interpretado=None,
            evidencia="El literal expresa mas de un valor posible.",
        )

    if re.search(r"consultar|cotizar|presupuesto|a convenir", raw, re.IGNORECASE):
        return PrecioReed(
            raw=raw_original,
            semantica=SemanticaPrecioReed.CONSULTAR,
            valor_interpretado=None,
            evidencia="La fuente exige consulta y no publica un valor numerico.",
        )

    motivo = NormalizadorPrecios.motivo_rechazo(raw)
    if motivo == "PRECIO_CERO_LITERAL":
        return PrecioReed(
            raw=raw_original,
            semantica=SemanticaPrecioReed.CERO,
            valor_interpretado=None,
            evidencia=(
                "El HTML publica cero literalmente; no demuestra gratuidad y "
                "el dominio no admite observaciones de precio cero."
            ),
        )
    if motivo == "PRECIO_AMBIGUO":
        return PrecioReed(
            raw=raw_original,
            semantica=SemanticaPrecioReed.AMBIGUO,
            valor_interpretado=None,
            evidencia="El literal no explicita si el valor esta expresado en miles.",
        )
    if motivo is None:
        precio = NormalizadorPrecios.normalizar(raw)
        return PrecioReed(
            raw=raw_original,
            semantica=SemanticaPrecioReed.EXACTO,
            valor_interpretado=precio.valor if precio else None,
            evidencia="El literal contiene un unico valor numerico representable.",
        )

    return PrecioReed(
        raw=raw_original,
        semantica=SemanticaPrecioReed.OTRO,
        valor_interpretado=None,
        evidencia=f"El guard central rechazo el literal: {motivo}.",
    )


def extraer_contexto_reed(html: str, url_fuente: str) -> ContextoReed:
    soup = BeautifulSoup(html or "", "html.parser")
    texto_pagina = _texto(soup)
    producto = _texto(soup.select_one("h1[itemprop='name']"))
    breadcrumb = [
        _texto(nodo)
        for nodo in soup.select(".breadcrumb [itemprop='name']")
        if _texto(nodo)
    ]
    categoria = breadcrumb[-2] if len(breadcrumb) >= 2 else ""
    precio_nodo = soup.select_one("[itemprop='offers'] [itemprop='price']")
    moneda_nodo = soup.select_one("[itemprop='offers'] [itemprop='priceCurrency']")
    disponibilidad_nodo = soup.select_one(
        "[itemprop='offers'] [itemprop='availability']"
    )
    precio_raw = _texto(precio_nodo)
    descripcion = soup.select_one("#product-description-short[itemprop='description']")
    iva = next(
        (
            _texto(nodo)
            for nodo in (descripcion.select("p") if descripcion else [])
            if re.search(r"incluyen\s+iva", _texto(nodo), re.IGNORECASE)
        ),
        "",
    )
    empresa = next(
        (
            _texto(nodo)
            for nodo in soup.select("footer *")
            if _texto(nodo).upper() == "REED TECHNOLOGY"
        ),
        "REED TECHNOLOGY",
    )
    ciudad = "Córdoba" if re.search(r"ciudad de C[oó]rdoba", texto_pagina, re.I) else ""

    return ContextoReed(
        empresa_raw=empresa,
        provincia_raw="Córdoba" if ciudad else "",
        ciudad_raw=ciudad,
        categoria_raw=categoria,
        producto_raw=producto,
        sku_raw=_texto(soup.select_one("[itemprop='sku']")),
        precio_producto_raw=precio_raw,
        precio_producto_semantica=clasificar_precio_reed(precio_raw).semantica,
        moneda_raw=(moneda_nodo.get("content", "") if moneda_nodo else ""),
        availability_raw=(
            disponibilidad_nodo.get("href", "") if disponibilidad_nodo else ""
        ),
        iva_incluido_raw=iva,
        url_origen=url_fuente,
        vigencia_raw="",
    )


def extraer_candidatos_reed(
    html: str,
    url_fuente: str,
    fecha_relevamiento: date | None = None,
) -> list[CandidatoReed]:
    fecha = fecha_relevamiento or date.today()
    soup = BeautifulSoup(html or "", "html.parser")
    contexto = extraer_contexto_reed(html, url_fuente)
    candidatos = [
        CandidatoReed(
            tipo_candidato="producto_contenedor",
            categoria_raw=contexto.categoria_raw,
            producto_raw=contexto.producto_raw,
            servicio_raw=contexto.producto_raw,
            descripcion_raw=contexto.producto_raw,
            precio=clasificar_precio_reed(contexto.precio_producto_raw),
            moneda=contexto.moneda_raw,
            empresa_raw=contexto.empresa_raw,
            provincia_raw=contexto.provincia_raw,
            ciudad_raw=contexto.ciudad_raw,
            modalidad_raw="",
            url_origen=url_fuente,
            fecha_relevamiento=fecha,
        )
    ]

    descripcion = soup.select_one("#product-description-short[itemprop='description']")
    if not descripcion:
        return candidatos

    for parrafo in descripcion.select("p"):
        descripcion_raw = _texto(parrafo)
        coincidencias = list(_PATRON_PRECIO.finditer(descripcion_raw))
        if not coincidencias:
            continue
        precio_match = coincidencias[-1]
        precio_raw = precio_match.group(0)
        servicio_raw = descripcion_raw[: precio_match.start()].strip(" .")
        if not servicio_raw:
            continue
        candidatos.append(
            CandidatoReed(
                tipo_candidato="servicio_descripto",
                categoria_raw=contexto.categoria_raw,
                producto_raw=contexto.producto_raw,
                servicio_raw=servicio_raw,
                descripcion_raw=descripcion_raw,
                precio=clasificar_precio_reed(precio_raw),
                moneda=contexto.moneda_raw,
                empresa_raw=contexto.empresa_raw,
                provincia_raw=contexto.provincia_raw,
                ciudad_raw=contexto.ciudad_raw,
                modalidad_raw="",
                url_origen=url_fuente,
                fecha_relevamiento=fecha,
            )
        )

    return candidatos


def parsear_ofertas_reed(
    html: str,
    url_fuente: str,
    fecha_relevamiento: date | None = None,
    rechazos: list[RechazoIngesta] | None = None,
) -> list[OfertaDTO]:
    ofertas: list[OfertaDTO] = []
    for candidato in extraer_candidatos_reed(
        html,
        url_fuente=url_fuente,
        fecha_relevamiento=fecha_relevamiento,
    ):
        if (
            candidato.precio.semantica is not SemanticaPrecioReed.EXACTO
            or candidato.precio.valor_interpretado is None
        ):
            if rechazos is not None:
                motivo = NormalizadorPrecios.motivo_rechazo(candidato.precio.raw)
                rechazos.append(
                    RechazoIngesta(
                        fuente=url_fuente,
                        razon=(
                            f"{candidato.tipo_candidato}: "
                            f"{motivo or candidato.precio.semantica.value.upper()} "
                            f"precio_raw={candidato.precio.raw!r}; "
                            f"evidencia={candidato.precio.evidencia}"
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
                equipo_raw=candidato.producto_raw,
                precio=candidato.precio.valor_interpretado,
                precio_raw=candidato.precio.raw,
                moneda=candidato.moneda,
                fecha_relevamiento=candidato.fecha_relevamiento,
            )
        )

    return ofertas
