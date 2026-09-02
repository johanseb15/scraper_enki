from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.dto.rechazo_ingesta import RechazoIngesta
from src.normalizadores.normalizador_precios import NormalizadorPrecios


@dataclass(frozen=True)
class ContextoDMR:
    empresa_raw: str
    provincia_raw: str
    ciudad_raw: str
    fecha_editorial_raw: str
    alcance_fecha_editorial: str
    textos_temporales_raw: tuple[str, ...]
    aviso_precio_raw: str
    modalidades_raw: tuple[str, ...]


@dataclass(frozen=True)
class CandidatoDMR:
    categoria_raw: str
    servicio_raw: str
    equipos_raw: tuple[str, ...]
    precio_raw: str
    precio_interpretado: int | None
    semantica_precio: str
    moneda: str
    modalidad_raw: str
    empresa_raw: str
    provincia_raw: str
    ciudad_raw: str
    fecha_editorial_raw: str
    url_origen: str
    fecha_relevamiento: date


def _texto(nodo) -> str:
    return nodo.get_text(" ", strip=True) if nodo else ""


def _empresa_raw(soup: BeautifulSoup) -> str:
    logo = soup.select_one(".nav-logo")
    if logo:
        texto_directo = " ".join(
            fragmento.strip()
            for fragmento in logo.find_all(string=True, recursive=False)
            if fragmento.strip()
        )
        if texto_directo:
            return texto_directo
    return "DMR Web Design"


def extraer_contexto_dmr(html: str) -> ContextoDMR:
    soup = BeautifulSoup(html or "", "html.parser")
    texto_pagina = soup.get_text(" ", strip=True)
    textos_temporales = tuple(
        dict.fromkeys(
            _texto(nodo)
            for nodo in soup.select(
                ".page-hero p, .section-title, .note-card, "
                "#precios h2, #precios .section-sub, #precios .note"
            )
            if re.search(r"abril\s+2026", _texto(nodo), re.IGNORECASE)
        )
    )
    coincidencia_fecha = re.search(r"abril\s+2026", " ".join(textos_temporales), re.IGNORECASE)
    hero_ubicacion = _texto(soup.select_one(".hero-badge, .hero-tag"))
    provincia = "Mendoza" if re.search(r"Mendoza", texto_pagina, re.IGNORECASE) else ""
    ciudad = "Mendoza Capital" if re.search(
        r"Mendoza\s+Capital", hero_ubicacion, re.IGNORECASE
    ) else provincia

    return ContextoDMR(
        empresa_raw=_empresa_raw(soup),
        provincia_raw=provincia,
        ciudad_raw=ciudad,
        fecha_editorial_raw=coincidencia_fecha.group(0) if coincidencia_fecha else "",
        alcance_fecha_editorial=(
            "lista_de_precios" if coincidencia_fecha else "no_determinado"
        ),
        textos_temporales_raw=textos_temporales,
        aviso_precio_raw=_texto(
            soup.select_one(
                ".note-card, #precios .section-sub, #precios .note"
            )
        ),
        modalidades_raw=tuple(
            _texto(nodo)
            for nodo in soup.select(".modality-title, .fcard h4")
            if _texto(nodo)
        ),
    )


def _semantica_precio(precio_raw: str) -> tuple[str, int | None, str | None]:
    motivo = NormalizadorPrecios.motivo_rechazo(precio_raw)
    if motivo is None:
        precio = NormalizadorPrecios.normalizar(precio_raw)
        return "exacto", precio.valor if precio else None, None

    texto = (precio_raw or "").strip()
    if motivo == "PRECIO_AUSENTE":
        return "sin_precio", None, motivo
    if re.search(r"\bdesde\b", texto, re.IGNORECASE):
        return "desde", None, motivo
    if re.search(r"\d\s*[–-]\s*\$?\s*\d", texto):
        return "rango", None, motivo
    if re.search(r"consultar|presupuesto|cotizar|a convenir", texto, re.IGNORECASE):
        return "consultar", None, motivo
    if motivo == "PRECIO_AMBIGUO":
        return "ambiguo", None, motivo
    return "otro", None, motivo


def extraer_candidatos_dmr(
    html: str,
    url_fuente: str,
    fecha_relevamiento: date | None = None,
) -> list[CandidatoDMR]:
    fecha = fecha_relevamiento or date.today()
    soup = BeautifulSoup(html or "", "html.parser")
    contexto = extraer_contexto_dmr(html)
    candidatos: list[CandidatoDMR] = []

    for tarjeta in soup.select(".service-card, .svc"):
        servicio_raw = _texto(
            tarjeta.select_one(".service-name, .svc-name")
        )
        if not servicio_raw:
            continue
        precio_raw = _texto(
            tarjeta.select_one(".service-price, .svc-price")
        )
        semantica, valor, _ = _semantica_precio(precio_raw)
        candidatos.append(
            CandidatoDMR(
                categoria_raw=(tarjeta.get("data-cat") or "").strip(),
                servicio_raw=servicio_raw,
                equipos_raw=tuple(
                    _texto(nodo)
                    for nodo in tarjeta.select(
                        ".device-tag, .svc-tags span"
                    )
                    if _texto(nodo)
                ),
                precio_raw=precio_raw,
                precio_interpretado=valor,
                semantica_precio=semantica,
                moneda="ARS" if "$" in precio_raw else "",
                modalidad_raw=_texto(tarjeta.select_one(".service-price-label")),
                empresa_raw=contexto.empresa_raw,
                provincia_raw=contexto.provincia_raw,
                ciudad_raw=contexto.ciudad_raw,
                fecha_editorial_raw=contexto.fecha_editorial_raw,
                url_origen=url_fuente,
                fecha_relevamiento=fecha,
            )
        )

    return candidatos


def parsear_ofertas_dmr(
    html: str,
    url_fuente: str,
    fecha_relevamiento: date | None = None,
    rechazos: list[RechazoIngesta] | None = None,
) -> list[OfertaDTO]:
    ofertas: list[OfertaDTO] = []
    for candidato in extraer_candidatos_dmr(
        html,
        url_fuente=url_fuente,
        fecha_relevamiento=fecha_relevamiento,
    ):
        motivo = NormalizadorPrecios.motivo_rechazo(candidato.precio_raw)
        if motivo or candidato.precio_interpretado is None:
            if rechazos is not None:
                rechazos.append(
                    RechazoIngesta(
                        fuente=url_fuente,
                        razon=(
                            f"{candidato.servicio_raw}: {motivo or 'PRECIO_NO_REPRESENTABLE'} "
                            f"precio_raw={candidato.precio_raw!r}"
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
                equipo_raw=" / ".join(candidato.equipos_raw),
                precio=candidato.precio_interpretado,
                precio_raw=candidato.precio_raw,
                moneda=candidato.moneda,
                fecha_relevamiento=candidato.fecha_relevamiento,
            )
        )

    return ofertas
