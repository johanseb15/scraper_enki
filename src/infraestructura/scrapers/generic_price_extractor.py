from __future__ import annotations

from datetime import datetime
import re

from bs4 import BeautifulSoup, Tag

from src.dominio.evidencia import (
    RegistroPrecioComercialObservado,
)


EXTRACTOR_VERSION = "generic_price_extractor_v2"


_PRICE_RE = re.compile(
    r"""
    (?:
        (?P<prefix>\$|ARS)\s*
    )
    (?P<number>
        \d{1,3}(?:[.,]\d{3})+(?:,\d{2})?
        |
        \d+(?:,\d{2})?
    )
    |
    (?P<number_suffix>
        \d{1,3}(?:[.,]\d{3})+(?:,\d{2})?
        |
        \d+(?:,\d{2})?
    )
    \s*
    (?P<suffix>ARS)
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _extraer_match_precio(texto: str) -> re.Match[str] | None:
    return _PRICE_RE.search(texto.strip())


def _normalizar_numero_precio(numero: str) -> int | None:
    valor = numero.strip().replace(" ", "")

    if "." in valor and "," in valor:
        if valor.rfind(",") > valor.rfind("."):
            entero, _, decimales = valor.partition(",")
            if decimales and set(decimales) != {"0"}:
                return None
            valor = entero.replace(".", "")
        else:
            return None

    elif "," in valor:
        partes = valor.split(",")

        if len(partes) == 2:
            izquierda, derecha = partes

            if len(derecha) == 3:
                valor = izquierda + derecha
            elif len(derecha) == 2:
                if set(derecha) != {"0"}:
                    return None
                valor = izquierda
            else:
                return None
        else:
            if all(len(parte) == 3 for parte in partes[1:]):
                valor = "".join(partes)
            else:
                return None

    elif "." in valor:
        partes = valor.split(".")

        if all(len(parte) == 3 for parte in partes[1:]):
            valor = "".join(partes)
        else:
            return None

    if not valor.isdigit():
        return None

    resultado = int(valor)

    if resultado <= 0:
        return None

    return resultado


def _normalizar_precio(
    texto: str,
) -> tuple[str, int, str] | None:
    raw = texto.strip()

    if not raw:
        return None

    match = _extraer_match_precio(raw)

    if match is None:
        return None

    numero = (
        match.group("number")
        or match.group("number_suffix")
    )

    value = _normalizar_numero_precio(numero)

    if value is None:
        return None

    price_raw = match.group(0).strip()

    return price_raw, value, "ARS"


def _normalizar_espacios(texto: str) -> str:
    return " ".join(texto.split()).strip()


def _texto_sin_precio(
    elemento: Tag,
    price_raw: str,
) -> str:
    texto = elemento.get_text(" ", strip=True)
    texto = texto.replace(price_raw, " ")
    return _normalizar_espacios(texto)


def _es_contexto_razonable(texto: str) -> bool:
    if not texto or texto == "UNKNOWN":
        return False

    palabras = texto.split()

    if len(palabras) > 40:
        return False

    if len(texto) > 320:
        return False

    return True


def _contexto_fila(
    elemento_precio: Tag,
    price_raw: str,
) -> str | None:
    fila = elemento_precio.find_parent("tr")

    if fila is None:
        return None

    partes: list[str] = []

    for celda in fila.find_all(["td", "th"], recursive=False):
        texto = celda.get_text(" ", strip=True)

        if price_raw in texto:
            texto = texto.replace(price_raw, " ")

        texto = _normalizar_espacios(texto)

        if texto:
            partes.append(texto)

    contexto = _normalizar_espacios(" ".join(partes))

    if _es_contexto_razonable(contexto):
        return contexto

    return None


def _contexto_hermano(
    elemento_precio: Tag,
) -> str | None:
    parent = elemento_precio.parent

    if not isinstance(parent, Tag):
        return None

    partes: list[str] = []

    for child in parent.children:
        if child is elemento_precio:
            continue

        if isinstance(child, Tag):
            texto = child.get_text(" ", strip=True)
        else:
            texto = str(child).strip()

        texto = _normalizar_espacios(texto)

        if texto:
            partes.append(texto)

    contexto = _normalizar_espacios(" ".join(partes))

    if _es_contexto_razonable(contexto):
        return contexto

    return None


def _contexto_ancestro_pequeno(
    elemento_precio: Tag,
    price_raw: str,
) -> str | None:
    actual = elemento_precio.parent
    profundidad = 0

    while isinstance(actual, Tag) and profundidad < 3:
        texto = _texto_sin_precio(
            actual,
            price_raw,
        )

        if _es_contexto_razonable(texto):
            return texto

        actual = actual.parent
        profundidad += 1

    return None


def _contexto_para_precio(
    elemento_precio: Tag,
    price_raw: str,
) -> str:
    contexto = _contexto_fila(
        elemento_precio,
        price_raw,
    )

    if contexto:
        return contexto

    contexto = _contexto_hermano(
        elemento_precio,
    )

    if contexto:
        return contexto

    contexto = _contexto_ancestro_pequeno(
        elemento_precio,
        price_raw,
    )

    if contexto:
        return contexto

    return "UNKNOWN"


def _elementos_precio_hoja(
    soup: BeautifulSoup,
) -> list[Tag]:
    candidatos: list[Tag] = []

    for elemento in soup.find_all(
        [
            "td",
            "span",
            "strong",
            "b",
            "p",
            "div",
            "li",
        ]
    ):
        texto = elemento.get_text(" ", strip=True)

        if _normalizar_precio(texto) is None:
            continue

        descendiente_con_precio = False

        for descendiente in elemento.find_all(
            [
                "td",
                "span",
                "strong",
                "b",
                "p",
                "div",
                "li",
            ]
        ):
            if descendiente is elemento:
                continue

            texto_desc = descendiente.get_text(
                " ",
                strip=True,
            )

            if _normalizar_precio(texto_desc) is not None:
                descendiente_con_precio = True
                break

        if descendiente_con_precio:
            continue

        candidatos.append(elemento)

    return candidatos


def _source_record_id(
    index: int,
    economic_object_raw: str,
    price_value: int,
) -> str:
    normalized_object = re.sub(
        r"\s+",
        "-",
        economic_object_raw.casefold(),
    ).strip("-")

    normalized_object = re.sub(
        r"[^a-z0-9áéíóúüñ\-]+",
        "",
        normalized_object,
    )

    return (
        f"generic:{index}:"
        f"{normalized_object}:"
        f"{price_value}"
    )


def extraer_observaciones_precio_genericas(
    html: str,
    *,
    source: str,
    provider: str,
    source_url: str,
    raw_document_id: int,
    retrieved_at: datetime,
    content_hash: str | None = None,
) -> list[
    RegistroPrecioComercialObservado
]:
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    observaciones: list[
        RegistroPrecioComercialObservado
    ] = []

    seen: set[
        tuple[str, int, str]
    ] = set()

    for elemento in _elementos_precio_hoja(soup):
        texto = elemento.get_text(
            " ",
            strip=True,
        )

        parsed = _normalizar_precio(texto)

        if parsed is None:
            continue

        price_raw, price_value, currency = parsed

        economic_object_raw = (
            _contexto_para_precio(
                elemento,
                price_raw,
            )
        )

        if (
            not economic_object_raw
            or economic_object_raw == "UNKNOWN"
        ):
            continue

        identity = (
            economic_object_raw,
            price_value,
            currency,
        )

        if identity in seen:
            continue

        seen.add(identity)

        metadata = {
            "retrieved_at": (
                retrieved_at.isoformat()
            ),
            "extraction_strategy": (
                "generic_html_price_context_v2"
            ),
        }

        if content_hash is not None:
            metadata["content_hash"] = (
                content_hash
            )

        observaciones.append(
            RegistroPrecioComercialObservado(
                raw_document_id=raw_document_id,
                source=source,
                source_record_id=(
                    _source_record_id(
                        len(observaciones),
                        economic_object_raw,
                        price_value,
                    )
                ),
                source_url=source_url,
                extractor_version=(
                    EXTRACTOR_VERSION
                ),
                extraction_status="EXTRACTED",
                provider_raw=provider,
                economic_object_raw=(
                    economic_object_raw
                ),
                scope_raw={
                    "raw_context": (
                        economic_object_raw
                    ),
                },
                price_raw=price_raw,
                price_value=price_value,
                currency_raw=currency,
                device_type_raw="UNKNOWN",
                operating_system_raw="UNKNOWN",
                backup_raw="UNKNOWN",
                drivers_raw="UNKNOWN",
                programs_raw="UNKNOWN",
                license_raw="UNKNOWN",
                modality_raw="UNKNOWN",
                comparable_status=(
                    "INDETERMINATE"
                ),
                metadata=metadata,
                rejection_reason="",
            )
        )

    return observaciones
