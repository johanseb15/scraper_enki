"""Caracterización reproducible de Informática Paraná, fuera del dominio de precios."""

from __future__ import annotations

from dataclasses import dataclass
import json

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class UnidadEstructuradaParana:
    tipo_oferta: str
    tipo_item: str
    nombre_raw: str
    descripcion_raw: str | None
    precio_raw: object | None
    price_specification_raw: object | None
    moneda_raw: str | None
    availability_raw: str | None
    provider_raw: object | None
    area_served_raw: tuple[str, ...]
    url_raw: str | None
    identificador_raw: str | None


@dataclass(frozen=True)
class CaracterizacionInformaticaParana:
    tipo_proveedor: str
    proveedor_raw: str
    descripcion_proveedor_raw: str
    url: str
    direccion_raw: str
    cobertura_raw: tuple[str, ...]
    moneda_aceptada_raw: str | None
    rango_precio_raw: str | None
    tipo_catalogo: str
    nombre_catalogo_raw: str
    unidades_estructuradas: tuple[UnidadEstructuradaParana, ...]
    senales_comerciales_raw: tuple[str, ...]
    rechazos: tuple[()] = ()

    @property
    def cantidad_precios(self) -> int:
        return sum(
            unidad.precio_raw is not None
            for unidad in self.unidades_estructuradas
        )

    @property
    def cantidad_ofertas_sin_precio(self) -> int:
        return sum(
            unidad.tipo_oferta == "Offer" and unidad.precio_raw is None
            for unidad in self.unidades_estructuradas
        )


def _texto(nodo) -> str:
    return nodo.get_text(" ", strip=True) if nodo else ""


def _nombres_area(valor) -> tuple[str, ...]:
    if not isinstance(valor, list):
        valor = [valor] if valor else []
    return tuple(
        item.get("name", "") if isinstance(item, dict) else str(item)
        for item in valor
        if item
    )


def _local_business(soup: BeautifulSoup) -> dict:
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            datos = json.loads(script.string or script.get_text())
        except (TypeError, json.JSONDecodeError):
            continue
        nodos = datos.get("@graph", []) if isinstance(datos, dict) else []
        if not nodos:
            nodos = [datos]
        for nodo in nodos:
            tipos = nodo.get("@type", []) if isinstance(nodo, dict) else []
            tipos = [tipos] if isinstance(tipos, str) else tipos
            if "LocalBusiness" in tipos:
                return nodo
    return {}


def caracterizar_informatica_parana(
    html: str,
) -> CaracterizacionInformaticaParana:
    soup = BeautifulSoup(html or "", "html.parser")
    negocio = _local_business(soup)
    catalogo = negocio.get("hasOfferCatalog") or {}
    unidades: list[UnidadEstructuradaParana] = []

    for oferta in catalogo.get("itemListElement", []):
        item = oferta.get("itemOffered") or {}
        unidades.append(
            UnidadEstructuradaParana(
                tipo_oferta=oferta.get("@type", ""),
                tipo_item=item.get("@type", ""),
                nombre_raw=item.get("name", ""),
                descripcion_raw=item.get("description"),
                precio_raw=oferta.get("price"),
                price_specification_raw=oferta.get("priceSpecification"),
                moneda_raw=oferta.get("priceCurrency"),
                availability_raw=oferta.get("availability"),
                provider_raw=item.get("provider") or oferta.get("seller"),
                area_served_raw=_nombres_area(item.get("areaServed")),
                url_raw=item.get("url") or oferta.get("url"),
                identificador_raw=item.get("@id") or oferta.get("@id"),
            )
        )

    direccion = negocio.get("address") or {}
    direccion_raw = ", ".join(
        parte
        for parte in (
            direccion.get("streetAddress"),
            direccion.get("addressLocality"),
            direccion.get("addressRegion"),
            direccion.get("addressCountry"),
        )
        if parte
    )
    senales = tuple(
        dict.fromkeys(
            _texto(nodo)
            for nodo in soup.select(".hero__desc, .promo-ticker__item")
            if _texto(nodo)
        )
    )

    return CaracterizacionInformaticaParana(
        tipo_proveedor=negocio.get("@type", ""),
        proveedor_raw=negocio.get("name", ""),
        descripcion_proveedor_raw=negocio.get("description", ""),
        url=negocio.get("url", ""),
        direccion_raw=direccion_raw,
        cobertura_raw=_nombres_area(negocio.get("areaServed")),
        moneda_aceptada_raw=negocio.get("currenciesAccepted"),
        rango_precio_raw=negocio.get("priceRange"),
        tipo_catalogo=catalogo.get("@type", ""),
        nombre_catalogo_raw=catalogo.get("name", ""),
        unidades_estructuradas=tuple(unidades),
        senales_comerciales_raw=senales,
    )
