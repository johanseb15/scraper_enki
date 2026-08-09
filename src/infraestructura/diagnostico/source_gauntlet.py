"""Diagnóstico de adquisición para fuentes reales, independiente del dominio."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests


class EstrategiaAdquisicion(str, Enum):
    API_OFFICIAL = "API_OFFICIAL"
    HTTP_STATIC = "HTTP_STATIC"
    WEB_STRUCTURED = "WEB_STRUCTURED"
    WEB_BROWSER = "WEB_BROWSER"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class Dificultad(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


@dataclass(frozen=True)
class FuenteDiagnostico:
    nombre: str
    url: str
    ubicacion_esperada: str | None = None
    tipo: str = "web"


@dataclass
class SenalesHtml:
    titulo: str = ""
    proveedor_posible: str = ""
    bytes_aproximados: int = 0
    tablas: int = 0
    items_aproximados: int = 0
    precios_aproximados: int = 0
    muestras_precio_raw: list[str] = field(default_factory=list)
    muestras_precio_numerico: list[int | float] = field(default_factory=list)
    monedas: list[str] = field(default_factory=list)
    json_ld: int = 0
    microdata: int = 0
    json_embebido: int = 0
    scripts_relevantes: int = 0
    indicios_spa_js: list[str] = field(default_factory=list)
    paginacion: bool = False
    links_detalle: list[str] = field(default_factory=list)
    ubicaciones_posibles: list[str] = field(default_factory=list)
    candidatos_raw: list[dict[str, Any]] = field(default_factory=list)
    servicios_productos_posibles: list[str] = field(default_factory=list)
    challenge_antibot: list[str] = field(default_factory=list)
    estrategia_sugerida: EstrategiaAdquisicion = EstrategiaAdquisicion.HTTP_STATIC
    dificultad: Dificultad = Dificultad.A
    problemas: list[str] = field(default_factory=list)


@dataclass
class ResultadoHttp:
    url_final: str
    status_http: int | None
    content_type: str | None
    tiempo_respuesta_s: float
    exito: bool
    error: str | None
    senales: SenalesHtml | None
    snapshot: str | None = None


@dataclass
class ResultadoBrowser:
    ejecutado: bool = False
    url_final: str | None = None
    status_http: int | None = None
    tiempo_respuesta_s: float | None = None
    exito: bool = False
    error: str | None = None
    senales: SenalesHtml | None = None
    informacion_solo_render: dict[str, Any] = field(default_factory=dict)
    requests_observadas: list[dict[str, Any]] = field(default_factory=list)
    snapshot: str | None = None


@dataclass
class ReporteFuente:
    fuente: FuenteDiagnostico
    timestamp: str
    http: ResultadoHttp
    browser: ResultadoBrowser
    estrategia_minima: EstrategiaAdquisicion
    dificultad: Dificultad
    problema_real: list[str]

    def to_dict(self) -> dict[str, Any]:
        return _serializar(asdict(self))


_PATRON_PRECIO = re.compile(
    r"(?<!\w)(?:AR\$|ARS|US\$|USD|U\$S|\$)\s*"
    r"\d[\d.\s]*(?:,\d{1,2})?",
    re.IGNORECASE,
)
_PATRONES_ANTIBOT = {
    "captcha_component": re.compile(r"captcha|recaptcha|hcaptcha", re.IGNORECASE),
    "cloudflare_challenge": re.compile(
        r"cf-chl|cloudflare.*(?:challenge|ray id)|just a moment",
        re.IGNORECASE,
    ),
    "access_denied": re.compile(
        r"access denied|acceso denegado|verify you are human|verifica que eres humano",
        re.IGNORECASE,
    ),
    "traffic_verification": re.compile(
        r"account-verification|negative[_ -]traffic|verificaci[oó]n de cuenta",
        re.IGNORECASE,
    ),
}


def _bloqueos_reales(challenges: Iterable[str]) -> list[str]:
    return [challenge for challenge in challenges if challenge != "captcha_component"]
_UBICACIONES = (
    "Buenos Aires",
    "Córdoba",
    "Rosario",
    "Santa Fe",
    "Mendoza",
    "Tucumán",
    "Salta",
    "Paraná",
    "Neuquén",
    "Argentina",
)


def _serializar(valor: Any) -> Any:
    if isinstance(valor, Enum):
        return valor.value
    if isinstance(valor, dict):
        return {clave: _serializar(item) for clave, item in valor.items()}
    if isinstance(valor, list):
        return [_serializar(item) for item in valor]
    return valor


def _unicos(valores: Iterable[str], limite: int = 10) -> list[str]:
    resultado: list[str] = []
    vistos: set[str] = set()
    for valor in valores:
        limpio = " ".join(str(valor).split()).strip()
        if limpio and limpio not in vistos:
            resultado.append(limpio)
            vistos.add(limpio)
        if len(resultado) >= limite:
            break
    return resultado


def _recorrer_json(valor: Any) -> Iterable[dict[str, Any]]:
    if isinstance(valor, dict):
        yield valor
        for item in valor.values():
            yield from _recorrer_json(item)
    elif isinstance(valor, list):
        for item in valor:
            yield from _recorrer_json(item)


def _precio_numerico_posible(valor: Any) -> int | float | None:
    """Interpreta formatos monetarios comunes sólo como señal diagnóstica."""
    coincidencia = re.search(r"\d[\d.,\s]*", str(valor or ""))
    if not coincidencia:
        return None
    numero = coincidencia.group(0).replace(" ", "")
    if "." in numero and "," in numero:
        if numero.rfind(",") > numero.rfind("."):
            numero = numero.replace(".", "").replace(",", ".")
        else:
            numero = numero.replace(",", "")
    elif "," in numero:
        decimales = len(numero.rsplit(",", 1)[1])
        numero = numero.replace(",", ".") if decimales <= 2 else numero.replace(",", "")
    elif "." in numero:
        decimales = len(numero.rsplit(".", 1)[1])
        if numero.count(".") > 1 or decimales == 3:
            numero = numero.replace(".", "")
    try:
        resultado = float(numero)
    except ValueError:
        return None
    return int(resultado) if resultado.is_integer() else resultado


def _candidatos_json_ld(soup: BeautifulSoup) -> tuple[int, list[dict[str, Any]]]:
    bloques_validos = 0
    candidatos: list[dict[str, Any]] = []
    for script in soup.select('script[type="application/ld+json"]'):
        contenido = script.string or script.get_text()
        try:
            datos = json.loads(contenido)
        except (TypeError, json.JSONDecodeError):
            continue
        bloques_validos += 1
        for nodo in _recorrer_json(datos):
            tipo = nodo.get("@type")
            tipos = {tipo} if isinstance(tipo, str) else set(tipo or [])
            if not tipos.intersection({"Product", "Service", "Offer", "ListItem"}):
                continue
            oferta = nodo.get("offers") if isinstance(nodo.get("offers"), dict) else {}
            candidato = {
                "tipo": sorted(tipos),
                "nombre_raw": nodo.get("name") or nodo.get("title") or nodo.get("item", {}).get("name") if isinstance(nodo.get("item"), dict) else nodo.get("name") or nodo.get("title"),
                "precio_raw": nodo.get("price") or oferta.get("price") or oferta.get("lowPrice"),
                "moneda": nodo.get("priceCurrency") or oferta.get("priceCurrency"),
                "url_detalle": nodo.get("url") or oferta.get("url"),
                "identificador_externo": nodo.get("sku") or nodo.get("productID"),
            }
            candidato["precio_numerico_posible"] = _precio_numerico_posible(
                candidato["precio_raw"]
            )
            candidatos.append({k: v for k, v in candidato.items() if v not in (None, "", [])})
    return bloques_validos, candidatos[:20]


def _detectar_precios(soup: BeautifulSoup, texto: str, candidatos: list[dict[str, Any]]) -> list[str]:
    encontrados = list(_PATRON_PRECIO.findall(texto))
    for nodo in soup.select('[itemprop="price"], [data-price], meta[property="product:price:amount"]'):
        valor = nodo.get("content") or nodo.get("data-price") or nodo.get_text(" ", strip=True)
        if valor:
            encontrados.append(str(valor))
    for candidato in candidatos:
        if candidato.get("precio_raw") is not None:
            moneda = candidato.get("moneda") or ""
            encontrados.append(f"{moneda} {candidato['precio_raw']}".strip())
    return _unicos(encontrados, limite=20)


def analizar_html(html: str, url: str = "") -> SenalesHtml:
    soup = BeautifulSoup(html or "", "html.parser")
    texto = soup.get_text(" ", strip=True)
    titulo = soup.title.get_text(" ", strip=True) if soup.title else ""
    sitio = soup.select_one('meta[property="og:site_name"]')
    proveedor = sitio.get("content", "").strip() if sitio else titulo

    json_ld, candidatos = _candidatos_json_ld(soup)
    precios = _detectar_precios(soup, texto, candidatos)
    precios_numericos = _unicos_numericos(
        _precio_numerico_posible(precio) for precio in precios
    )

    selectores_item = (
        "article",
        '[itemtype*="Product"]',
        '[itemtype*="Service"]',
        '[class*="product"]',
        '[class*="producto"]',
        '[class*="service"]',
        '[class*="servicio"]',
        '[class*="item"]',
    )
    items = {id(nodo) for selector in selectores_item for nodo in soup.select(selector)}
    microdata = len(soup.select("[itemscope], [itemprop]"))

    scripts_json = soup.select(
        'script[type="application/json"], script#__NEXT_DATA__, script[data-state]'
    )
    scripts = soup.find_all("script")
    scripts_relevantes = sum(
        1
        for script in scripts
        if any(
            marca in ((script.get("src") or "") + " " + (script.get("id") or "")).lower()
            for marca in ("app", "main", "chunk", "next", "nuxt", "woocommerce", "webpack")
        )
    )

    indicios_js: list[str] = []
    html_lower = (html or "").lower()
    for marca in ("__next_data__", "__nuxt__", "webpack", "data-reactroot", "ng-version"):
        if marca in html_lower:
            indicios_js.append(marca)
    if soup.select_one("#root, #app, #__next"):
        indicios_js.append("contenedor_app")
    if len(scripts) >= 15 and len(texto) < 1500:
        indicios_js.append("muchos_scripts_poco_texto")

    challenges = [nombre for nombre, patron in _PATRONES_ANTIBOT.items() if patron.search(html or "")]
    tipos_estructurados = {
        tipo
        for candidato in candidatos
        for tipo in candidato.get("tipo", [])
    }
    estructura_comercial = bool(
        tipos_estructurados.intersection({"Product", "Service", "Offer"})
        or soup.select_one(
            '[itemprop="price"], [itemprop="offers"], '
            '[itemtype*="Product"], [itemtype*="Service"]'
        )
        or (scripts_json and items)
    )
    paginacion = bool(
        soup.select_one('a[rel="next"], .pagination, .paginacion, [class*="pagination"]')
        or re.search(r"\b(siguiente|next|página\s+\d+)\b", texto, re.IGNORECASE)
    )

    links = []
    for enlace in soup.find_all("a", href=True):
        href = urljoin(url, enlace["href"])
        etiqueta = enlace.get_text(" ", strip=True)
        combinado = f"{href} {etiqueta}".lower()
        if any(marca in combinado for marca in ("servicio", "repar", "product", "producto", "item", "detalle", "tienda")):
            links.append(href)

    encabezados = [n.get_text(" ", strip=True) for n in soup.select("h1, h2, h3, article a")]
    nombres_json = [str(c.get("nombre_raw", "")) for c in candidatos]
    servicios = _unicos([*nombres_json, *encabezados], limite=20)
    ubicaciones = [ubicacion for ubicacion in _UBICACIONES if ubicacion.casefold() in texto.casefold()]

    problemas: list[str] = []
    bloqueos = _bloqueos_reales(challenges)
    if bloqueos:
        estrategia = EstrategiaAdquisicion.BLOCKED
        dificultad = Dificultad.E
        problemas.append("challenge o bloqueo anti-bot")
    elif estructura_comercial:
        estrategia = EstrategiaAdquisicion.WEB_STRUCTURED
        dificultad = Dificultad.C
    elif indicios_js and not (precios or candidatos or len(items) >= 2):
        estrategia = EstrategiaAdquisicion.WEB_BROWSER
        dificultad = Dificultad.D
        problemas.append("contenido comercial no visible sin render")
    elif precios or items or soup.find("table"):
        estrategia = EstrategiaAdquisicion.HTTP_STATIC
        dificultad = Dificultad.B if len(items) > 10 or len(soup.find_all("table")) > 1 else Dificultad.A
    else:
        estrategia = EstrategiaAdquisicion.HTTP_STATIC
        dificultad = Dificultad.B
        problemas.append("sin candidatos comerciales claros")

    if precios and not any(moneda in " ".join(precios).upper() for moneda in ("$", "ARS", "USD", "US$")):
        problemas.append("precio sin moneda explícita")
    if not precios:
        problemas.append("sin precios detectables")
    if "captcha_component" in challenges and not bloqueos:
        problemas.append("CAPTCHA presente en componente no bloqueante")

    monedas: list[str] = []
    texto_precios = " ".join(precios).upper()
    if "ARS" in texto_precios or "$" in texto_precios:
        monedas.append("ARS/$")
    if "USD" in texto_precios or "US$" in texto_precios or "U$S" in texto_precios:
        monedas.append("USD")

    return SenalesHtml(
        titulo=titulo,
        proveedor_posible=proveedor,
        bytes_aproximados=len((html or "").encode("utf-8")),
        tablas=len(soup.find_all("table")),
        items_aproximados=len(items),
        precios_aproximados=len(precios),
        muestras_precio_raw=precios[:10],
        muestras_precio_numerico=precios_numericos[:10],
        monedas=monedas,
        json_ld=json_ld,
        microdata=microdata,
        json_embebido=len(scripts_json),
        scripts_relevantes=scripts_relevantes,
        indicios_spa_js=_unicos(indicios_js),
        paginacion=paginacion,
        links_detalle=_unicos(links),
        ubicaciones_posibles=ubicaciones,
        candidatos_raw=candidatos[:10],
        servicios_productos_posibles=servicios,
        challenge_antibot=challenges,
        estrategia_sugerida=estrategia,
        dificultad=dificultad,
        problemas=_unicos(problemas),
    )


def comparar_senales(http: SenalesHtml | None, browser: SenalesHtml | None) -> dict[str, Any]:
    if not browser:
        return {}
    http = http or SenalesHtml()
    return {
        "bytes_extra": max(0, browser.bytes_aproximados - http.bytes_aproximados),
        "items_extra": max(0, browser.items_aproximados - http.items_aproximados),
        "precios_extra": max(0, browser.precios_aproximados - http.precios_aproximados),
        "json_ld_extra": max(0, browser.json_ld - http.json_ld),
        "links_detalle_extra": [link for link in browser.links_detalle if link not in http.links_detalle][:10],
        "muestras_precio_nuevas": [p for p in browser.muestras_precio_raw if p not in http.muestras_precio_raw][:10],
    }


def _guardar_snapshot(snapshot_dir: Path | None, nombre: str, sufijo: str, contenido: str) -> str | None:
    if snapshot_dir is None:
        return None
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    seguro = re.sub(r"[^a-z0-9]+", "_", nombre.casefold()).strip("_")
    ruta = snapshot_dir / f"{seguro}.{sufijo}.html"
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)


def _unicos_numericos(valores: Iterable[int | float | None]) -> list[int | float]:
    resultado: list[int | float] = []
    for valor in valores:
        if valor is not None and valor not in resultado:
            resultado.append(valor)
    return resultado


def _texto_respuesta(respuesta: requests.Response) -> str:
    """Evita el fallback ISO-8859-1 de requests en HTML UTF-8 sin charset."""
    encoding = (respuesta.encoding or "").casefold()
    aparente = respuesta.apparent_encoding
    if aparente and (not encoding or encoding in {"iso-8859-1", "latin-1"}):
        respuesta.encoding = aparente
    return respuesta.text


def _diagnosticar_http(
    fuente: FuenteDiagnostico,
    timeout: float,
    snapshot_dir: Path | None,
) -> tuple[ResultadoHttp, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.7",
    }
    inicio = time.perf_counter()
    try:
        respuesta = requests.get(fuente.url, headers=headers, timeout=timeout, allow_redirects=True)
        duracion = time.perf_counter() - inicio
        html = _texto_respuesta(respuesta)
        senales = analizar_html(html, respuesta.url)
        bloqueos = _bloqueos_reales(senales.challenge_antibot)
        exito = respuesta.ok and not bloqueos
        if bloqueos:
            error = f"challenge anti-bot: {', '.join(bloqueos)}"
        else:
            error = None if exito else f"HTTP {respuesta.status_code}"
        return (
            ResultadoHttp(
                url_final=respuesta.url,
                status_http=respuesta.status_code,
                content_type=respuesta.headers.get("content-type"),
                tiempo_respuesta_s=round(duracion, 3),
                exito=exito,
                error=error,
                senales=senales,
                snapshot=_guardar_snapshot(snapshot_dir, fuente.nombre, "http", html),
            ),
            html,
        )
    except Exception as exc:
        duracion = time.perf_counter() - inicio
        return (
            ResultadoHttp(
                url_final=fuente.url,
                status_http=None,
                content_type=None,
                tiempo_respuesta_s=round(duracion, 3),
                exito=False,
                error=f"{type(exc).__name__}: {exc}",
                senales=None,
            ),
            "",
        )


def _requiere_browser(resultado: ResultadoHttp) -> bool:
    if not resultado.exito:
        return True
    if not resultado.senales:
        return True
    return resultado.senales.estrategia_sugerida == EstrategiaAdquisicion.WEB_BROWSER


def _diagnosticar_browser(
    fuente: FuenteDiagnostico,
    http: ResultadoHttp,
    timeout: float,
    snapshot_dir: Path | None,
) -> ResultadoBrowser:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return ResultadoBrowser(ejecutado=True, error=f"Playwright no disponible: {exc}")

    inicio = time.perf_counter()
    observadas: list[dict[str, Any]] = []
    try:
        with sync_playwright() as playwright:
            navegador = playwright.chromium.launch(headless=True)
            pagina = navegador.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
                ),
                locale="es-AR",
            )

            def registrar(respuesta):
                if len(observadas) >= 80:
                    return
                tipo = respuesta.request.resource_type
                if tipo in {"xhr", "fetch", "document"}:
                    observadas.append(
                        {"url": respuesta.url, "status": respuesta.status, "tipo": tipo}
                    )

            pagina.on("response", registrar)
            respuesta = pagina.goto(
                fuente.url,
                wait_until="domcontentloaded",
                timeout=int(timeout * 1000),
            )
            pagina.wait_for_timeout(2000)
            html = pagina.content()
            url_final = pagina.url
            status = respuesta.status if respuesta else None
            navegador.close()

        senales = analizar_html(html, url_final)
        return ResultadoBrowser(
            ejecutado=True,
            url_final=url_final,
            status_http=status,
            tiempo_respuesta_s=round(time.perf_counter() - inicio, 3),
            exito=(status is None or status < 400)
            and not _bloqueos_reales(senales.challenge_antibot),
            senales=senales,
            informacion_solo_render=comparar_senales(http.senales, senales),
            requests_observadas=observadas,
            snapshot=_guardar_snapshot(snapshot_dir, fuente.nombre, "browser", html),
        )
    except Exception as exc:
        return ResultadoBrowser(
            ejecutado=True,
            tiempo_respuesta_s=round(time.perf_counter() - inicio, 3),
            exito=False,
            error=f"{type(exc).__name__}: {exc}",
            requests_observadas=observadas,
        )


def diagnosticar_fuente(
    fuente: FuenteDiagnostico,
    browser: str = "auto",
    timeout: float = 20,
    snapshot_dir: Path | None = None,
) -> ReporteFuente:
    http, _ = _diagnosticar_http(fuente, timeout, snapshot_dir)
    ejecutar_browser = browser == "always" or (browser == "auto" and _requiere_browser(http))
    resultado_browser = (
        _diagnosticar_browser(fuente, http, timeout, snapshot_dir)
        if ejecutar_browser
        else ResultadoBrowser()
    )

    senales_finales = resultado_browser.senales if resultado_browser.exito else http.senales
    if (
        http.senales
        and _bloqueos_reales(http.senales.challenge_antibot)
        and not resultado_browser.exito
    ):
        estrategia = EstrategiaAdquisicion.BLOCKED
        dificultad = Dificultad.E
    elif resultado_browser.ejecutado and resultado_browser.exito:
        estrategia = EstrategiaAdquisicion.WEB_BROWSER
        dificultad = Dificultad.D
    elif http.exito and senales_finales:
        estrategia = senales_finales.estrategia_sugerida
        dificultad = senales_finales.dificultad
    else:
        estrategia = EstrategiaAdquisicion.FAILED
        dificultad = Dificultad.E

    problemas: list[str] = []
    if http.error:
        problemas.append(http.error)
    if http.senales:
        problemas.extend(http.senales.problemas)
    if resultado_browser.error:
        problemas.append(resultado_browser.error)
    if resultado_browser.senales:
        problemas.extend(resultado_browser.senales.problemas)

    return ReporteFuente(
        fuente=fuente,
        timestamp=datetime.now(timezone.utc).isoformat(),
        http=http,
        browser=resultado_browser,
        estrategia_minima=estrategia,
        dificultad=dificultad,
        problema_real=_unicos(problemas, limite=20),
    )


def _api_get(url: str, token: str | None, timeout: float) -> dict[str, Any]:
    headers = {"User-Agent": "Enki-Source-Gauntlet/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    inicio = time.perf_counter()
    try:
        respuesta = requests.get(url, headers=headers, timeout=timeout)
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = {"raw": respuesta.text[:1000]}
        return {
            "url": url,
            "status": respuesta.status_code,
            "tiempo_s": round(time.perf_counter() - inicio, 3),
            "exito": respuesta.ok,
            "auth_required": respuesta.status_code in {401, 403} and not token,
            "respuesta": cuerpo,
        }
    except Exception as exc:
        return {
            "url": url,
            "status": None,
            "tiempo_s": round(time.perf_counter() - inicio, 3),
            "exito": False,
            "auth_required": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def diagnosticar_api_mercadolibre(timeout: float = 20) -> dict[str, Any]:
    """Prueba sólo recursos públicos/documentados de la API oficial de Mercado Libre."""
    token = os.getenv("MELI_ACCESS_TOKEN")
    categorias = _api_get("https://api.mercadolibre.com/sites/MLA/categories", token, timeout)
    busqueda = _api_get(
        "https://api.mercadolibre.com/sites/MLA/search?q=notebook&limit=3",
        token,
        timeout,
    )

    categorias_interes: list[dict[str, Any]] = []
    if categorias.get("exito") and isinstance(categorias.get("respuesta"), list):
        categorias_interes = [
            item
            for item in categorias["respuesta"]
            if any(marca in item.get("name", "").casefold() for marca in ("comput", "servicio", "tecnolog"))
        ]

    campos_items: list[dict[str, Any]] = []
    ids: list[str] = []
    cuerpo_busqueda = busqueda.get("respuesta")
    if busqueda.get("exito") and isinstance(cuerpo_busqueda, dict):
        for item in cuerpo_busqueda.get("results", [])[:3]:
            ids.append(str(item.get("id")))
            campos_items.append(
                {
                    clave: item.get(clave)
                    for clave in (
                        "id",
                        "title",
                        "price",
                        "original_price",
                        "currency_id",
                        "category_id",
                        "seller",
                        "permalink",
                        "address",
                        "attributes",
                        "date_created",
                        "last_updated",
                    )
                    if clave in item
                }
            )

    multiget = None
    if ids:
        atributos = "id,title,price,original_price,currency_id,category_id,seller_id,permalink,attributes,date_created,last_updated"
        multiget = _api_get(
            f"https://api.mercadolibre.com/items?ids={','.join(ids)}&attributes={atributos}",
            token,
            timeout,
        )

    auth_required = any(
        resultado and resultado.get("auth_required")
        for resultado in (categorias, busqueda, multiget)
    )
    estrategia = (
        EstrategiaAdquisicion.AUTH_REQUIRED
        if auth_required and not any(r and r.get("exito") for r in (categorias, busqueda, multiget))
        else EstrategiaAdquisicion.API_OFFICIAL
    )
    return _serializar(
        {
            "site": "MLA",
            "token_presente": bool(token),
            "estrategia": estrategia,
            "categorias": categorias,
            "categorias_interes": categorias_interes,
            "busqueda_items": busqueda,
            "campos_interes_muestra": campos_items,
            "multiget": multiget,
            "vendedores": "no intentado sin contrato/token aplicable",
            "documentacion": [
                "https://developers.mercadolibre.com.ar/es_ar/api-docs-es/items-y-busquedas",
                "https://developers.mercadolibre.com.ar/es_ar/publica-productos/obtencion-del-access-token",
            ],
        }
    )
