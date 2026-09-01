from __future__ import annotations
import re, unicodedata
from src.aplicacion.language_query_contract import *
from src.dominio.price_scope_contract import normalize_price_scope
from src.dominio.commercial_context import (
    CommercialContextOrigin,
    resolve_commercial_context,
)
from src.dominio.user_query_understanding import (
    UserQueryMonetaryComponent,
    UserQueryMonetaryComponentOrigin,
    UserQueryMonetaryComponentRole,
)

RULES=[
("FORMATEO_INSTALACION_SO",(r"\bformate",r"\binstal(?:ar|acion de) windows\b",r"\breinstalar windows\b")),
("BACKUP_DATOS",(r"\bbackup\b",r"\bback up\b",r"\brespaldo\b",r"\brespaldar\b",r"\bcopia de seguridad\b")),
("RECUPERACION_DATOS",(r"\brecuperacion de datos\b",r"\brecuperar (?:fotos|archivos|datos)\b")),
("LIMPIEZA_MANTENIMIENTO",(r"\blimpieza\b",r"\bpasta termica\b",r"\brepaste",r"\bmantenimiento preventivo\b")),
("ELIMINACION_MALWARE",(r"\bmalware\b",r"\bvirus\b",r"\bspyware\b")),
("INSTALACION_DRIVERS",(r"\bdrivers?\b",r"\bcontroladores\b")),
("INSTALACION_PROGRAMAS",(r"\binstalar (?:programas?|office|antivirus)\b",r"\bprogramas? basicos\b")),
("SOPORTE_REMOTO",(r"\bsoporte remoto\b",r"\basistencia remota\b",r"\ba distancia\b",r"\bteamviewer\b",r"\banydesk\b",r"\bacceso remoto\b")),
("ARMADO_PC",(
    r"\barmado de pc\b",
    r"\barmar (?:una|la) pc\b",
    r"\barmar pc\b",
    r"\b(?:la|una) pc\b[^.!?]{0,120}\barmarla\b",
    r"\bensambl",
)),
("UPGRADE_HARDWARE",(
    r"\bupgrade\b",
    r"\bmejorar la compu\b",
    r"\bcambio de hdd por ssd\b",
    r"\bampliacion de memoria\b",
    r"\b(?:cambio|cambiar|cambie) (?:el |un )?(?:disco|ssd)\b",
    r"\binstal(?:ar|acion de) (?:un |el )?ssd\b",
    r"\bponer (?:un |el )?ssd\b",
)),
("CLONADO_DISCO",(
    r"\bclonad[oa]\b",
    r"\bclonar\b",
    r"\bclonacion\b",
)),
("DIAGNOSTICO_REVISION",(r"\bdiagnostico\b",r"\brevision\b")),
("REPARACION_HARDWARE",(
    r"\breparar\b",
    r"\breparacion\b",
    r"\bcambio de pantalla\b",
    r"\bcambiar (?:un |el |la )?pantalla\b",
    r"\bcambio de teclado\b",
    r"\bcambiar (?:un |el |la )?teclado\b",
    r"\bcambio de fuente\b",
    r"\bcambiar (?:una |la )?fuente\b",
    r"\bbisagra\b",
    r"\bconector de carga\b",
)),
("VISITA_TECNICA_DOMICILIO",(r"\ba domicilio\b",r"\btecnico a casa\b",r"\ben el domicilio\b",r"\bvisita tecnica\b")),
("SERVICIO_IMPRESORAS",(r"\bimpresora",)),
("CCTV_INSTALACION_MANO_OBRA",(r"\bcamaras? (?:de seguridad|ip)\b",r"\bcctv\b",r"\bdvr\b")),
("WEB_LANDING",(r"\blanding page\b",)),
("WEB_SITIO_INSTITUCIONAL",(r"\bsitio institucional\b",r"\bweb institucional\b")),
("WEB_ECOMMERCE",(r"\becommerce\b",r"\btienda online\b",r"\bcarrito de compras\b")),
("WEB_MANTENIMIENTO",(r"\bmantenimiento (?:de )?(?:web|wordpress)\b",)),
("HOSTING_ADMINISTRADO",(r"\bhosting\b",)),
("VPS_ADMINISTRADO",(r"\bvps\b",)),
("DESARROLLO_SOFTWARE_HORA",(
    r"\bprogramacion\b",
    r"\bdesarrollo (?:web|de software)\b",
    r"\bdesarrollo (?:full ?stack|frontend|backend)\b",
)),
]
REMOTE={"SOPORTE_REMOTO","WEB_LANDING","WEB_SITIO_INSTITUCIONAL","WEB_ECOMMERCE","WEB_MANTENIMIENTO","HOSTING_ADMINISTRADO","VPS_ADMINISTRADO","DESARROLLO_SOFTWARE_HORA"}

PRICE_SCOPE_REQUIRED_SERVICES = frozenset({
    "SOPORTE_REMOTO",
    "VISITA_TECNICA_DOMICILIO",
})
PROV={"caba":"CABA","capital federal":"CABA","capital":"CABA","buenos aires":"Buenos Aires","bs as":"Buenos Aires","cordoba":"Córdoba","santa fe":"Santa Fe","mendoza":"Mendoza","tucuman":"Tucumán","salta":"Salta","jujuy":"Jujuy","chaco":"Chaco","corrientes":"Corrientes","entre rios":"Entre Ríos","neuquen":"Neuquén","rio negro":"Río Negro","chubut":"Chubut","santa cruz":"Santa Cruz","tierra del fuego":"Tierra del Fuego","la pampa":"La Pampa","san juan":"San Juan","san luis":"San Luis","la rioja":"La Rioja","catamarca":"Catamarca","formosa":"Formosa","misiones":"Misiones","santiago del estero":"Santiago del Estero"}
CITIES={"rosario":("Santa Fe","Rosario"),"la plata":("Buenos Aires","La Plata"),"mar del plata":("Buenos Aires","Mar del Plata"),"lanus":("Buenos Aires","Lanús"),"quilmes":("Buenos Aires","Quilmes"),"moreno":("Buenos Aires","Moreno"),"posadas":("Misiones","Posadas"),"comodoro rivadavia":("Chubut","Comodoro Rivadavia"),"zona norte":("Buenos Aires","Zona Norte"),"zona oeste":("Buenos Aires","Zona Oeste"),"zona sur":("Buenos Aires","Zona Sur"),"gba":("Buenos Aires","GBA"),"gran buenos aires":("Buenos Aires","GBA")}
BUY=(r"\bme quieren cobrar\b",r"\bme cobran\b",r"\bme cobraron\b",r"\bme pasaron\b",r"\bme presupuestaron\b",r"\bme cotizaron\b",r"\bme dijeron\b",r"\bpagar\b",r"\bme ofrecieron\b",r"\bme ofrecen\b")
SELL=(r"\bquiero cobrar\b",r"\bcuanto cobrar\b",r"\bcuanto cobro\b",r"\bcuanto le cobro\b",r"\bcuanto puedo cobrar\b",r"\ble puedo cobrar\b",r"\bdeberia cobrar\b",r"\bestoy cobrando\b",r"\byo cobre\b",r"\bcuanto pedir\b",r"\bquiero vender\b",r"\bvoy a vender\b",r"\bvendo\b")
EVAL=(r"\besta bien\b",r"\bte parece bien\b",r"\bconviene\b",r"\bes mucho\b",r"\bes caro\b",r"\besta caro\b",r"\bes barato\b",r"\bme estan matando\b",r"\bme estan afanando\b",r"\bme quedo corto\b",r"\bme estoy pasando\b",r"\brazonable\b")
HW=(r"\b(?:rtx|gtx|rx)\s?\d{3,4}\b",r"\bryzen\s+[3579]\b",r"\bcore\s+i[3579]\b",r"\bi[3579]\b",r"\bssd\b",r"\bnvme\b",r"\bmemoria ram\b",r"\bnotebook\b.*\b(?:nueva|usada|precio|sale|vender|vendo)\b",r"\bpc armada\b",r"\b(?:una|la) pc\s+(?:para|con)\b")

def fold(t):
    x=unicodedata.normalize("NFD",t.lower()); x="".join(c for c in x if unicodedata.category(c)!="Mn")
    return re.sub(r"\s+"," ",x).strip()
def has(t,ps): return any(re.search(p,fold(t),re.I) for p in ps)
def scalar_num(s):
    """Parse a scalar used with magnitude words such as lucas/mil/palos."""
    s=s.strip().lower().replace(" ","").replace(",",".")
    if s.count(".")>1:
        head,*tail=s.split(".")
        s=head+"."+"".join(tail)
    return float(s)

def money_num(s):
    """Parse a complete monetary amount without losing Argentine thousands separators."""
    s=s.strip().lower().replace(" ","")
    if not s:
        raise ValueError("empty money number")
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            return float(s.replace(".","").replace(",","."))
        return float(s.replace(",",""))
    if "." in s:
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
            return float(s.replace(".",""))
        return float(s)
    if "," in s:
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+", s):
            return float(s.replace(",",""))
        return float(s.replace(",","."))
    return float(s)
def _naked_number_is_non_price_context(x:str,m:re.Match)->bool:
    """Reject strong quantity/spec/model contexts for otherwise naked numbers."""
    before=fold(x[max(0,m.start()-24):m.start()])
    after=fold(x[m.end():m.end()+32])

    # Hardware model identifiers: RTX 4060, GTX 1660, RX 7600.
    if re.search(r"\b(?:rtx|gtx|rx)\s*$",before):
        return True

    # Quantities and technical specifications are not monetary amounts.
    if re.match(
        r"\s*(?:puestos?|camaras?|equipos?|unidades?|usuarios?|licencias?|"
        r"gb|tb|mb|mhz|ghz|hz|w|watts?|pulgadas?|inch(?:es)?)\b",
        after,
    ):
        return True

    return False

def _has_multiple_monetary_mentions(t:str)->bool:
    x=t.lower()

    # A true range is one economic price expression, not two independent prices.
    range_pattern=(
        r"\bentre\s+[\d.,]+\s+y\s+[\d.,]+\s*"
        r"(?:lucas?|mil|k|palos?|usd|u\$s|d[oó]lares?)\b"
    )
    x=re.sub(range_pattern," RANGE_PRICE ",x)

    patterns=(
        r"\b[\d.,]+\s*(?:lucas?|mil|k|palos?)\b",
        r"\b[\d.,]+\s*(?:usd|u\$s|d[oó]lares?)\b",
        r"(?<!\w)\$\s*[\d.]+(?:,\d+)?",
        r"\bun palo\b",
    )

    spans=[]
    for pattern in patterns:
        for m in re.finditer(pattern,x,re.I):
            span=m.span()
            if not any(span[0] < other[1] and other[0] < span[1] for other in spans):
                spans.append(span)

    return len(spans) > 1

def _price_type_from_scope(text: str) -> PriceType:
    scope = normalize_price_scope(text, has_price=True).comparison_scope
    return {
        "PER_HOUR": PriceType.PER_HOUR,
        "PER_MONTH": PriceType.PER_MONTH,
        "PER_VISIT": PriceType.PER_VISIT,
        "PER_UNIT": PriceType.PER_UNIT,
    }.get(scope, PriceType.EXACT)


def price(t):
    x=t.lower()
    m=re.search(r"\bentre\s+([\d.,]+)\s+y\s+([\d.,]+)\s*(lucas?|mil|k|palos?|usd|d[oó]lares?)\b",x)
    if m:
        a,b,u=m.groups(); a=scalar_num(a); b=scalar_num(b); cur="USD" if u in {"usd","dolares","dólares"} else "ARS"
        mult=1_000_000 if u.startswith("palo") else (1000 if u in {"k","mil","luca","lucas"} else 1)
        return PriceMention(PriceType.RANGE,min=a*mult,max=b*mult,currency=cur,raw_expression=m.group(0))
    m=re.search(r"\b(casi|aprox(?:imadamente)?|alrededor de)?\s*([\d.,]+)\s*(lucas?|mil|k|palos?)\b",x)
    if m:
        approx=bool(m.group(1)); v=scalar_num(m.group(2)); u=m.group(3); v*=1_000_000 if u.startswith("palo") else 1000
        pt=_price_type_from_scope(t)
        return PriceMention(pt,v,currency="ARS",raw_expression=m.group(0),is_approximate=approx)
    if re.search(r"\bun palo\b",x): return PriceMention(PriceType.EXACT,1_000_000,currency="ARS",raw_expression="un palo")
    m=re.search(r"\b([\d.,]+)\s*(usd|u\$s|d[oó]lares?)\b",x)
    if m:
        pt=_price_type_from_scope(t)
        return PriceMention(pt,money_num(m.group(1)),currency="USD",raw_expression=m.group(0))
    m=re.search(r"(?<!\w)\$\s*([\d.]+(?:,\d+)?)",x)
    if m: return PriceMention(PriceType.EXACT,money_num(m.group(1)),currency="ARS",raw_expression=m.group(0))
    m=re.search(
        r"(?<![\w$])(\d{1,3}(?:[.,]\d{3})+(?:,\d{1,2})?|\d{2,}(?:[.,]\d+)?)\b",
        x,
    )
    if m:
        # Guardrail: a naked number followed by a temporal unit is context, not money.
        # Examples: "hace 45 días", "hace 30 horas", "hace 12 meses".
        # `x` is lower-cased but still preserves accents. Normalize the tail
        # before matching temporal units so "días"/"años" behave like
        # "dias"/"anos".
        tail=fold(x[m.end():])
        if re.match(r"\s*(?:dias?|horas?|semanas?|mes(?:es)?|anos?|minutos?)\b",tail):
            return PriceMention()
        if _naked_number_is_non_price_context(x,m):
            return PriceMention()
        return PriceMention(PriceType.EXACT,money_num(m.group(1)),currency="UNKNOWN",raw_expression=m.group(0))
    return PriceMention()


_CONTEXTUAL_MONEY_PATTERN = re.compile(
    r"(?<!\w)"
    r"(\d{1,3}(?:[.,]\d{3})+(?:,\d{1,2})?"
    r"|\d{2,}(?:[.,]\d+)?)\b"
)


def _component_currency(
    text: str,
    match: re.Match,
) -> str:
    before = fold(
        text[max(0, match.start() - 12):match.start()]
    )
    after = fold(
        text[match.end():match.end() + 16]
    )

    if re.search(r"\$\s*$", before):
        return "ARS"

    if re.match(
        r"\s*(?:usd|u\$s|dolares?)\b",
        after,
    ):
        return "USD"

    return "UNKNOWN"


def _component_role(
    text: str,
    match: re.Match,
) -> UserQueryMonetaryComponentRole | None:
    before = fold(
        text[max(0, match.start() - 64):match.start()]
    )
    role_before = re.sub(
        r"(?:\$|ars|usd|u\$s)\s*$",
        "",
        before,
    ).rstrip()
    around = fold(
        text[
            max(0, match.start() - 72):
            min(len(text), match.end() + 40)
        ]
    )

    if re.search(
        r"\b(?:yo\s+)?cobre\s*$|\btotal\s*$",
        role_before,
    ):
        return UserQueryMonetaryComponentRole.TOTAL_CHARGED

    has_material = bool(
        re.search(
            r"\b(?:pendrive|repuesto|materiales?|ssd|disco|"
            r"fuente|teclado|pantalla)\b",
            around,
        )
    )

    if has_material and re.search(
        r"\b(?:sale|cuesta|costo|vale)\s*$",
        role_before,
    ):
        return UserQueryMonetaryComponentRole.MATERIAL_COST

    return None


def _monetary_composition(
    text: str,
) -> tuple[UserQueryMonetaryComponent, ...]:
    if not re.search(
        r"\bmano de obra\b",
        fold(text),
    ):
        return ()

    by_role: dict[
        UserQueryMonetaryComponentRole,
        list[UserQueryMonetaryComponent],
    ] = {}

    for match in _CONTEXTUAL_MONEY_PATTERN.finditer(text):
        if _naked_number_is_non_price_context(
            text,
            match,
        ):
            continue

        role = _component_role(
            text,
            match,
        )

        if role is None:
            continue

        by_role.setdefault(
            role,
            [],
        ).append(
            UserQueryMonetaryComponent(
                role=role,
                value=money_num(match.group(1)),
                currency=_component_currency(
                    text,
                    match,
                ),
                origin=(
                    UserQueryMonetaryComponentOrigin.EXPLICIT
                ),
                raw_expression=match.group(1),
            )
        )

    total_items = by_role.get(
        UserQueryMonetaryComponentRole.TOTAL_CHARGED,
        [],
    )
    material_items = by_role.get(
        UserQueryMonetaryComponentRole.MATERIAL_COST,
        [],
    )

    if (
        len(total_items) != 1
        or len(material_items) != 1
    ):
        return ()

    total = total_items[0]
    material = material_items[0]
    components = [
        total,
        material,
    ]

    if (
        total.currency == material.currency
        and total.value >= material.value
    ):
        components.append(
            UserQueryMonetaryComponent(
                role=UserQueryMonetaryComponentRole.LABOR,
                value=total.value - material.value,
                currency=total.currency,
                origin=(
                    UserQueryMonetaryComponentOrigin.DERIVED
                ),
                derivation_method=(
                    "TOTAL_CHARGED_MINUS_MATERIAL_COST"
                ),
                derived_from=(
                    UserQueryMonetaryComponentRole.TOTAL_CHARGED,
                    UserQueryMonetaryComponentRole.MATERIAL_COST,
                ),
            )
        )

    return tuple(components)


def geo(t):
    x=fold(t)
    for raw,(p,c) in CITIES.items():
        if re.search(rf"\b{re.escape(raw)}\b",x): return Geography(raw,p,c)
    for raw,p in PROV.items():
        if re.search(rf"\b{re.escape(raw)}\b",x): return Geography(raw,p,None)
    return Geography()
def services(t):
    x=fold(t); out=[]
    for c,ps in RULES:
        if any(re.search(p,x,re.I) for p in ps): out.append(c)
    out=list(dict.fromkeys(out))

    if "UPGRADE_HARDWARE" in out and "CLONADO_DISCO" in out:
        out=[c for c in out if c!="UPGRADE_HARDWARE"]

    # A domicile visit is a standalone service only when it is the economic
    # object itself. When another concrete local service is present, domicilio
    # is delivery/modality scope, not a second priced service.
    if "VISITA_TECNICA_DOMICILIO" in out and len(out)>1:
        out=[c for c in out if c!="VISITA_TECNICA_DOMICILIO"]
    return tuple(out)
def device(t):
    x=fold(t)
    for d,ps in [("NOTEBOOK",(r"\bnotebook\b",r"\blaptop\b",r"\bnote\b")),("PC",(r"\bpc\b",r"\bcompu\b",r"\bcomputadora\b")),("CELULAR",(r"\bcelular\b",r"\bcelu\b")),("IMPRESORA",(r"\bimpresora\b",)),("GPU",(r"\bplaca de video\b",r"\bgpu\b",r"\b(?:rtx|gtx|rx)\s?\d{3,4}\b")),("STORAGE",(r"\bssd\b",r"\bnvme\b",r"\bdisco\b",r"\bpendrive\b"))]:
        if any(re.search(p,x) for p in ps): return d
    return None
def parts(t):
    x=fold(t)
    if re.search(r"\b(?:solo|solamente) (?:de )?(?:la )?mano de obra\b|\bsin repuesto\b",x): return PartsScope.LABOR_ONLY
    if (
        re.search(r"\bmano de obra\b", x)
        and re.search(
            r"\b(?:el |la )?(?:repuesto|ssd|disco|fuente|teclado|pantalla)\b"
            r"[^.!?]{0,40}\bva aparte\b",
            x,
        )
    ):
        return PartsScope.LABOR_ONLY
    if re.search(r"\bincluye (?:el |la |los |las )?(?:repuesto|panel|pantalla|ssd|fuente|teclado|materiales)\b",x): return PartsScope.PARTS_INCLUDED
    if re.search(r"\bya (?:tengo|compre|compro) (?:el |la )?(?:repuesto|ssd|fuente|teclado|pantalla)\b",x): return PartsScope.USER_PROVIDED
    return PartsScope.UNKNOWN



def _has_explicit_economic_intent(t:str)->bool:
    x=fold(t)
    return has(t,BUY) or has(t,SELL) or has(t,EVAL) or bool(re.search(
        r"\bcuanto\b|\bprecio\b|\bcobrar\b|\bpagar\b|\$|\b(?:lucas?|mil|k|palos?|usd|u\$s|d[oó]lares?)\b",
        x,
    ))

def _technical_need(t:str)->TechnicalNeed|None:
    x=fold(t)
    windows_installation=bool(re.search(r"\b(?:instalando|instalar|instalacion de)\s+windows\b|\bwindows\s+\d+\b",x))
    blocked_progress=bool(re.search(r"\b(?:se queda|queda|quedo|se quedo|se congela|congelado|clavado|trabado|colgado)\b",x))
    progress_marker=bool(re.search(r"\b\d{1,3}\s*%\b|\bpor ciento\b",x))
    asks_cause=bool(re.search(r"\bque puede estar pasando\b|\bque pasa\b|\bpor que\b|\bcual puede ser\b",x))
    if windows_installation and blocked_progress and (progress_marker or asks_cause):
        return TechnicalNeed(
            domain="PC",
            technical_problem="OS_INSTALLATION_FAILURE",
            economic_intent_explicit=_has_explicit_economic_intent(t),
            candidate_routes=(
                "DIAGNOSTIC_SERVICE",
                "OS_INSTALLATION_SERVICE",
                "HARDWARE_DIAGNOSTIC",
            ),
            product_purchase_recommendation="NONE_YET",
            clarification_required=True,
        )
    return None

def parse_pricing_query(raw_text:str,*,language_evidence_type:str="UNKNOWN")->ParsedPricingQuery:
    x=fold(raw_text)
    tech=_technical_need(raw_text)
    if tech is not None and not tech.economic_intent_explicit:
        g=geo(raw_text)
        return ParsedPricingQuery(
            raw_text,
            x,
            IntentAction.UNKNOWN,
            IntentSide.UNKNOWN,
            EconomicObjectKind.UNKNOWN,
            (),
            MarketScope.UNKNOWN,
            ServiceModality.UNKNOWN,
            PriceMention(),
            g,
            "PC",
            "UNKNOWN",
            False,
            resolve_commercial_context(
                raw_text,
                origin=CommercialContextOrigin.USER_CLAIM,
            ),
            ParseMetadata(
                0.8,
                True,
                "TECHNICAL_NEED_CLARIFICATION_REQUIRED",
                "Necesito confirmar contexto técnico antes de convertir esto en una decisión económica.",
                explicit_fields=("technical_need.raw_problem",),
                derived_fields=("technical_need.candidate_routes",),
            ),
            language_evidence_type,
            query_kind=QueryKind.TECHNICAL_NEED,
            technical_need=tech,
        )
    components = _monetary_composition(
        raw_text,
    )
    p=price(raw_text); g=geo(raw_text); sv=services(raw_text); dev=device(raw_text); ps=parts(raw_text)
    total_component = next(
        (
            item
            for item in components
            if item.role
            is UserQueryMonetaryComponentRole.TOTAL_CHARGED
        ),
        None,
    )
    if total_component is not None:
        p = PriceMention(
            PriceType.EXACT,
            total_component.value,
            currency=total_component.currency,
            raw_expression=total_component.raw_expression,
        )
    component_roles = {
        item.role
        for item in components
    }
    if {
        UserQueryMonetaryComponentRole.MATERIAL_COST,
        UserQueryMonetaryComponentRole.LABOR,
    } <= component_roles:
        ps = PartsScope.PARTS_INCLUDED
    explicit=[]; inferred=[]; derived=[]
    has_price=p.value is not None or p.min is not None
    scope=normalize_price_scope(
        raw_text,
        has_price=has_price,
        is_range=p.type is PriceType.RANGE,
    )
    if has_price: explicit.append("price")
    for component in components:
        field = (
            "monetary_component."
            + component.role.value.lower()
        )
        if (
            component.origin
            is UserQueryMonetaryComponentOrigin.EXPLICIT
        ):
            explicit.append(field)
        else:
            derived.append(field)
    if p.currency=="ARS" and re.search(r"\b(?:lucas?|mil|k|palos?)\b|\$",raw_text,re.I): inferred.append("price.currency")
    if g.raw_location:
        explicit.append("geography.raw_location")
        if g.city: inferred.append("geography.province")
    if dev: explicit.append("device_type")
    if sv: derived.append("canonical_services")
    side=IntentSide.SELL if has(raw_text,SELL) else IntentSide.BUY if (has(raw_text,BUY) or (has_price and re.search(r"\bme piden\b",x))) else IntentSide.UNKNOWN
    if has(raw_text,EVAL) and has_price: action=IntentAction.EVALUATE_PRICE
    elif (
        side==IntentSide.BUY
        and re.search(r"\bcuanto deberia pagar\b",x)
    ):
        action=IntentAction.SUGGEST_PRICE
    elif re.search(r"\bcuanto(?: le)? cobro\b",x): action=IntentAction.SUGGEST_PRICE
    elif side==IntentSide.SELL and not has_price: action=IntentAction.SUGGEST_PRICE
    elif (
        side==IntentSide.SELL
        and has_price
        and re.search(r"\byo cobre\b",x)
    ):
        action=IntentAction.EVALUATE_PRICE
    elif re.search(r"\bcompar",x): action=IntentAction.COMPARE
    elif re.search(
        r"\bcuanto (?:(?:sale|cuesta|esta)|(?:se )?esta cobrando|estan cobrando|se cobra|cobran)\b"
        r"|\bprecio de referencia\b|\bprecio de\b",
        x,
    ):
        action=IntentAction.MARKET_REFERENCE
    elif has_price and side in {IntentSide.BUY,IntentSide.SELL}: action=IntentAction.EVALUATE_PRICE
    else: action=IntentAction.UNKNOWN
    hardware=has(raw_text,HW) and not sv
    kind=EconomicObjectKind.HARDWARE if hardware else EconomicObjectKind.BUNDLE if len(sv)>1 else EconomicObjectKind.SERVICE if len(sv)==1 else EconomicObjectKind.UNKNOWN
    if hardware: market=MarketScope.GOODS; mod=ServiceModality.UNKNOWN
    elif sv and all(s in REMOTE for s in sv): market=MarketScope.REMOTE_NATIONAL; mod=ServiceModality.REMOTE; derived+=["market_scope","modality"]
    elif sv:
        market=MarketScope.LOCAL; derived.append("market_scope")
        mod=ServiceModality.ONSITE if re.search(r"\ba domicilio\b|\btecnico a casa\b|\ben (?:mi|el) domicilio\b",x) else ServiceModality.WORKSHOP if re.search(r"\ben taller\b|\ben el local\b|\blo llevo\b",x) else ServiceModality.UNKNOWN
        if mod!=ServiceModality.UNKNOWN: explicit.append("modality")
    else: market=MarketScope.UNKNOWN; mod=ServiceModality.UNKNOWN
    reasons=[]; question=None
    explicit_components = tuple(
        item
        for item in components
        if item.origin
        is UserQueryMonetaryComponentOrigin.EXPLICIT
    )
    monetary_composition_resolved = {
        UserQueryMonetaryComponentRole.TOTAL_CHARGED,
        UserQueryMonetaryComponentRole.MATERIAL_COST,
        UserQueryMonetaryComponentRole.LABOR,
    } <= component_roles
    if (
        (
            _has_multiple_monetary_mentions(raw_text)
            or len(explicit_components) > 1
        )
        and not monetary_composition_resolved
    ):
        reasons+=["MULTIPLE_MONETARY_MENTIONS"]
        question="Detecté más de un monto en la consulta. ¿Qué importe querés evaluar y a qué unidad de cobro corresponde?"
    if market==MarketScope.LOCAL and not g.province: reasons+=["MISSING_PROVINCE"]; question=question or "¿En qué provincia se realiza el servicio?"
    if kind==EconomicObjectKind.UNKNOWN: reasons+=["UNKNOWN_ECONOMIC_OBJECT"]; question=question or "¿Qué servicio o producto tecnológico querés evaluar?"
    if p.currency=="UNKNOWN" and has_price: reasons+=["UNKNOWN_CURRENCY"]; question=question or "¿Ese monto está expresado en pesos argentinos o en otra moneda?"
    if kind==EconomicObjectKind.BUNDLE: reasons+=["BUNDLE_REQUIRES_COMPARABLE_SCOPE"]
    if (
        len(sv)==1
        and sv[0] in PRICE_SCOPE_REQUIRED_SERVICES
        and scope.comparison_scope=="UNKNOWN"
        and action in {
            IntentAction.EVALUATE_PRICE,
            IntentAction.SUGGEST_PRICE,
            IntentAction.MARKET_REFERENCE,
        }
    ):
        reasons+=["PRICE_SCOPE_REQUIRED"]
        question=question or "?Ese precio corresponde a una hora, una visita, un abono mensual u otra unidad de cobro?"
    if re.search(r"\b(?:(?:cambio de )|(?:cambiar (?:un |una |el |la )?))(?:pantalla|teclado|fuente|ssd|disco)\b",x) and ps==PartsScope.UNKNOWN:
        reasons+=["UNKNOWN_PARTS_SCOPE"]; question=question or "¿El precio incluye el repuesto o es sólo mano de obra?"
    blocking={
        "MISSING_PROVINCE",
        "UNKNOWN_ECONOMIC_OBJECT",
        "UNKNOWN_CURRENCY",
        "UNKNOWN_PARTS_SCOPE",
        "MULTIPLE_MONETARY_MENTIONS",
        "PRICE_SCOPE_REQUIRED",
    }
    clar=bool(blocking & set(reasons)); conf=max(0.0,round(.95-(.25 if clar else 0)-(.15 if action==IntentAction.UNKNOWN else 0)-(.20 if kind==EconomicObjectKind.UNKNOWN else 0),2))
    commercial_context = resolve_commercial_context(
        raw_text,
        origin=CommercialContextOrigin.USER_CLAIM,
    ).with_parts_scope(ps)
    return ParsedPricingQuery(raw_text,x,action,side,kind,sv,market,mod,p,g,dev,"USED" if re.search(r"\busad[oa]\b",x) else "NEW" if re.search(r"\bnuev[oa]\b",x) else "UNKNOWN",kind==EconomicObjectKind.BUNDLE,commercial_context,ParseMetadata(conf,clar,"|".join(reasons) if reasons else None,question,tuple(dict.fromkeys(explicit)),tuple(dict.fromkeys(inferred)),tuple(dict.fromkeys(derived))),language_evidence_type,price_scope=scope,monetary_components=components)
