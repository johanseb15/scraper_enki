from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from statistics import median
import re

from src.dominio.market_observation import MarketObservation
from src.normalizadores.normalizador_precios import NormalizadorPrecios


def money(value: Decimal) -> str:
    return format(value, ".2f") if value == value.quantize(Decimal(".01")) else format(value, "f")


def query_market(observations: list[MarketObservation], *, service: str,
                 province: str | None = None, city: str | None = None,
                 currency: str | None = None, modality: str | None = None,
                 own_price: str | None = None, own_currency: str = "ARS",
                 own_unit: str | None = None, own_scope: str | None = None,
                 own_modality: str | None = None) -> dict:
    own = None
    if own_price is not None:
        normalized = NormalizadorPrecios.normalizar(own_price)
        if normalized is None or normalized.valor <= 0:
            raise ValueError("Ingresá un precio exacto positivo, por ejemplo 1.299,50.")
        if re.search(r"USD|ARS|US\$|U\$S|AR\$",own_price,re.IGNORECASE) and normalized.moneda != own_currency:
            raise ValueError("La moneda del precio propio no coincide con el grupo elegido.")
        own = normalized.valor
    unique = {}
    for o in observations:
        if o.id in unique and unique[o.id] != o:
            raise ValueError("Una identidad de observación contiene datos conflictivos.")
        unique[o.id] = o
    selected = sorted((o for o in unique.values() if o.service == service
                       and (not province or (o.province or "").casefold() == province.casefold())
                       and (not city or (o.city or "").casefold() == city.casefold())
                       and (not currency or o.currency == currency)
                       and (not modality or o.modality == modality)), key=lambda o: o.id)
    groups = defaultdict(list)
    offers = []
    for o in selected:
        reason = o.exclusion_reason()
        offers.append({"id": o.id, "provider": o.provider, "service": o.service,
                       "price": money(o.oferta.precio.valor) if o.oferta else None,
                       "currency": o.currency, "modality": o.modality, "unit": o.unit,
                       "scope": o.scope, "province": o.province, "city": o.city,
                       "source_url": o.source_url, "captured_at": o.captured_at,
                       "effective_date": o.effective_date,
                       "capture_url": f"/market/captures/{o.capture_id}" if o.capture_id else None,
                       "raw": o.raw, "exclusion_reason": reason,
                       "comparability_note": o.comparability_note})
        if reason is None:
            # Cada dimensión económica forma parte de la identidad del grupo.
            groups[(o.currency, o.modality, o.unit, o.scope)].append(o)
    benchmarks = []
    hypotheses = []
    for (ccy, mode, unit, scope), items in sorted(groups.items()):
        values = [i.oferta.precio.valor for i in items]
        mid = median(values)
        difference = None
        if (own is not None and own_currency == ccy
                and (own_unit is None or own_unit == unit)
                and (own_scope is None or own_scope == scope)
                and (own_modality is None or own_modality == mode)):
            difference = format(((own - mid) / mid * 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP), ".2f")
        ids = [i.id for i in items]
        benchmarks.append({"currency": ccy, "modality": mode, "unit": unit, "scope": scope,
                           "offer_count": len(items),
                           "provider_count": len({i.provider.strip().casefold() for i in items}),
                           "min": money(min(values)), "median": money(mid), "max": money(max(values)),
                           "own_price_difference_pct": difference, "evidence_ids": ids})
        hypotheses.append({"title": "Validar alcance y condiciones antes de cotizar",
                           "reason": f"Se observaron {len(items)} precios publicados para {scope}. Verificar tareas incluidas, impuestos y condiciones puede ayudar a definir una propuesta comparable.",
                           "next_step": "Solicitar confirmación de vigencia y una cotización con el mismo alcance.",
                           "evidence_ids": ids})
    if any(o.exclusion_reason() for o in selected):
        hypotheses.append({"title": "Investigar ofertas que no publican condiciones suficientes",
                           "reason": "Hay ofertas observadas con dimensiones sin establecer; explicitar alcance y modalidad merece validación comercial.",
                           "next_step": "Consultar al proveedor y contrastar con entrevistas a clientes; no se infiere demanda.",
                           "evidence_ids": [o.id for o in selected if o.exclusion_reason()]})
    return {"service": service, "offer_count": len(selected),
            "provider_count": len({o.provider.strip().casefold() for o in selected}),
            "offers": offers, "benchmarks": benchmarks, "hypotheses": hypotheses,
            "unanswered": ["Demanda y tamaño de mercado", "Rentabilidad y costos del proveedor",
                           "Tendencias históricas", "Vigencia efectiva de precios sin confirmación",
                           "Impuestos, garantías y tareas no detalladas por la fuente"],
            "limitations": ["Muestra pequeña y dirigida; no representa todo el mercado argentino.",
                            "La captura prueba lo publicado en esa fecha; no garantiza vigencia actual.",
                            "La ubicación indica lo publicado por el proveedor; no implica cobertura de atención.",
                            "Un grupo con un solo proveedor es una referencia individual.",
                            "Las oportunidades son hipótesis para investigar, sin inferir demanda o rentabilidad."]}
