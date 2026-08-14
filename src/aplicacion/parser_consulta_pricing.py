from __future__ import annotations
import re, unicodedata
from src.aplicacion.language_query_contract import *

RULES=[
("FORMATEO_INSTALACION_SO",(r"\bformate",r"\binstal(?:ar|acion de) windows\b",r"\breinstalar windows\b")),
("BACKUP_DATOS",(r"\bbackup\b",r"\bback up\b",r"\brespaldo\b",r"\brespaldar\b",r"\bcopia de seguridad\b")),
("RECUPERACION_DATOS",(r"\brecuperacion de datos\b",r"\brecuperar (?:fotos|archivos|datos)\b")),
("LIMPIEZA_MANTENIMIENTO",(r"\blimpieza\b",r"\bpasta termica\b",r"\brepaste",r"\bmantenimiento preventivo\b")),
("ELIMINACION_MALWARE",(r"\bmalware\b",r"\bvirus\b",r"\bspyware\b")),
("INSTALACION_DRIVERS",(r"\bdrivers?\b",r"\bcontroladores\b")),
("INSTALACION_PROGRAMAS",(r"\binstalar (?:programas?|office|antivirus)\b",r"\bprogramas? basicos\b")),
("SOPORTE_REMOTO",(r"\bsoporte remoto\b",r"\basistencia remota\b",r"\ba distancia\b",r"\bteamviewer\b",r"\banydesk\b",r"\bacceso remoto\b")),
("ARMADO_PC",(r"\barmado de pc\b",r"\barmar una pc\b",r"\barmar pc\b",r"\bensambl")),
("UPGRADE_HARDWARE",(r"\bupgrade\b",r"\bmejorar la compu\b",r"\bcambio de hdd por ssd\b",r"\bampliacion de memoria\b")),
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
("DESARROLLO_SOFTWARE_HORA",(r"\bprogramacion\b",r"\bdesarrollo (?:web|de software)\b")),
]
REMOTE={"SOPORTE_REMOTO","WEB_LANDING","WEB_SITIO_INSTITUCIONAL","WEB_ECOMMERCE","WEB_MANTENIMIENTO","HOSTING_ADMINISTRADO","VPS_ADMINISTRADO","DESARROLLO_SOFTWARE_HORA"}
PROV={"caba":"CABA","capital federal":"CABA","buenos aires":"Buenos Aires","bs as":"Buenos Aires","cordoba":"Córdoba","santa fe":"Santa Fe","mendoza":"Mendoza","tucuman":"Tucumán","salta":"Salta","jujuy":"Jujuy","chaco":"Chaco","corrientes":"Corrientes","entre rios":"Entre Ríos","neuquen":"Neuquén","rio negro":"Río Negro","chubut":"Chubut","santa cruz":"Santa Cruz","tierra del fuego":"Tierra del Fuego","la pampa":"La Pampa","san juan":"San Juan","san luis":"San Luis","la rioja":"La Rioja","catamarca":"Catamarca","formosa":"Formosa","misiones":"Misiones","santiago del estero":"Santiago del Estero"}
CITIES={"rosario":("Santa Fe","Rosario"),"la plata":("Buenos Aires","La Plata"),"mar del plata":("Buenos Aires","Mar del Plata"),"lanus":("Buenos Aires","Lanús"),"quilmes":("Buenos Aires","Quilmes"),"moreno":("Buenos Aires","Moreno"),"posadas":("Misiones","Posadas"),"comodoro rivadavia":("Chubut","Comodoro Rivadavia"),"zona norte":("Buenos Aires","Zona Norte"),"zona oeste":("Buenos Aires","Zona Oeste"),"zona sur":("Buenos Aires","Zona Sur"),"gba":("Buenos Aires","GBA"),"gran buenos aires":("Buenos Aires","GBA")}
BUY=(r"\bme quieren cobrar\b",r"\bme cobran\b",r"\bme cobraron\b",r"\bme pasaron\b",r"\bme presupuestaron\b",r"\bme cotizaron\b",r"\bme dijeron\b",r"\bpagar\b",r"\bme ofrecieron\b")
SELL=(r"\bquiero cobrar\b",r"\bcuanto cobrar\b",r"\ble puedo cobrar\b",r"\bdeberia cobrar\b",r"\bcuanto pedir\b")
EVAL=(r"\besta bien\b",r"\bte parece bien\b",r"\bes mucho\b",r"\bes caro\b",r"\besta caro\b",r"\bes barato\b",r"\bme estan matando\b",r"\bme estan afanando\b",r"\bme quedo corto\b",r"\bme estoy pasando\b",r"\brazonable\b")
HW=(r"\b(?:rtx|gtx|rx)\s?\d{3,4}\b",r"\bryzen\s+[3579]\b",r"\bcore\s+i[3579]\b",r"\bi[3579]\b",r"\bssd\b",r"\bnvme\b",r"\bmemoria ram\b",r"\bnotebook\b.*\b(?:nueva|usada|precio|sale)\b",r"\bpc armada\b",r"\b(?:una|la) pc\s+(?:para|con)\b")

def fold(t):
    x=unicodedata.normalize("NFD",t.lower()); x="".join(c for c in x if unicodedata.category(c)!="Mn")
    return re.sub(r"\s+"," ",x).strip()
def has(t,ps): return any(re.search(p,fold(t),re.I) for p in ps)
def num(s):
    s=s.strip().lower().replace(" ","").replace(",",".")
    if s.count(".")>1: s=s.replace(".","")
    return float(s)
def price(t):
    x=t.lower()
    m=re.search(r"\bentre\s+([\d.,]+)\s+y\s+([\d.,]+)\s*(lucas?|mil|k|palos?|usd|d[oó]lares?)\b",x)
    if m:
        a,b,u=m.groups(); a=num(a); b=num(b); cur="USD" if u in {"usd","dolares","dólares"} else "ARS"
        mult=1_000_000 if u.startswith("palo") else (1000 if u in {"k","mil","luca","lucas"} else 1)
        return PriceMention(PriceType.RANGE,min=a*mult,max=b*mult,currency=cur,raw_expression=m.group(0))
    m=re.search(r"\b(casi|aprox(?:imadamente)?|alrededor de)?\s*([\d.,]+)\s*(lucas?|mil|k|palos?)\b",x)
    if m:
        approx=bool(m.group(1)); v=num(m.group(2)); u=m.group(3); v*=1_000_000 if u.startswith("palo") else 1000
        pt=PriceType.PER_HOUR if re.search(r"\bpor hora\b|\bla hora\b",x) else PriceType.PER_MONTH if re.search(r"\bpor mes\b|\bal mes\b|\bmensual\b",x) else PriceType.PER_VISIT if re.search(r"\bpor visita\b",x) else PriceType.PER_UNIT if re.search(r"\bpor (?:equipo|unidad|pc)\b",x) else PriceType.EXACT
        return PriceMention(pt,v,currency="ARS",raw_expression=m.group(0),is_approximate=approx)
    if re.search(r"\bun palo\b",x): return PriceMention(PriceType.EXACT,1_000_000,currency="ARS",raw_expression="un palo")
    m=re.search(r"\b([\d.,]+)\s*(usd|u\$s|d[oó]lares?)\b",x)
    if m:
        pt=PriceType.PER_HOUR if re.search(r"\bpor hora\b|\bla hora\b",x) else PriceType.PER_MONTH if re.search(r"\bpor mes\b|\bal mes\b|\bmensual\b",x) else PriceType.PER_VISIT if re.search(r"\bpor visita\b",x) else PriceType.PER_UNIT if re.search(r"\bpor (?:equipo|unidad|pc)\b",x) else PriceType.EXACT
        return PriceMention(pt,num(m.group(1)),currency="USD",raw_expression=m.group(0))
    m=re.search(r"(?<!\w)\$\s*([\d.]+(?:,\d+)?)",x)
    if m: return PriceMention(PriceType.EXACT,num(m.group(1)),currency="ARS",raw_expression=m.group(0))
    m=re.search(r"(?<![\w$])(\d{2,}(?:[.,]\d+)?)\b",x)
    if m:
        # Guardrail: a naked number followed by a temporal unit is context, not money.
        # Examples: "hace 45 días", "hace 30 horas", "hace 12 meses".
        # `x` is lower-cased but still preserves accents. Normalize the tail
        # before matching temporal units so "días"/"años" behave like
        # "dias"/"anos".
        tail=fold(x[m.end():])
        if re.match(r"\s*(?:dias?|horas?|semanas?|mes(?:es)?|anos?|minutos?)\b",tail):
            return PriceMention()
        return PriceMention(PriceType.EXACT,num(m.group(1)),currency="UNKNOWN",raw_expression=m.group(0))
    return PriceMention()
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
    if re.search(r"\bsolo (?:la )?mano de obra\b|\bsin repuesto\b",x): return PartsScope.LABOR_ONLY
    if re.search(r"\bincluye (?:el |la |los |las )?(?:repuesto|panel|pantalla|ssd|fuente|teclado|materiales)\b",x): return PartsScope.PARTS_INCLUDED
    if re.search(r"\bya (?:tengo|compre) (?:el |la )?(?:repuesto|ssd|fuente|teclado|pantalla)\b",x): return PartsScope.USER_PROVIDED
    return PartsScope.UNKNOWN

def parse_pricing_query(raw_text:str,*,language_evidence_type:str="UNKNOWN")->ParsedPricingQuery:
    x=fold(raw_text); p=price(raw_text); g=geo(raw_text); sv=services(raw_text); dev=device(raw_text); ps=parts(raw_text)
    explicit=[]; inferred=[]; derived=[]
    has_price=p.value is not None or p.min is not None
    if has_price: explicit.append("price")
    if p.currency=="ARS" and re.search(r"\b(?:lucas?|mil|k|palos?)\b|\$",raw_text,re.I): inferred.append("price.currency")
    if g.raw_location:
        explicit.append("geography.raw_location")
        if g.city: inferred.append("geography.province")
    if dev: explicit.append("device_type")
    if sv: derived.append("canonical_services")
    side=IntentSide.SELL if has(raw_text,SELL) else IntentSide.BUY if has(raw_text,BUY) else IntentSide.UNKNOWN
    if has(raw_text,EVAL) and has_price: action=IntentAction.EVALUATE_PRICE
    elif side==IntentSide.SELL and not has_price: action=IntentAction.SUGGEST_PRICE
    elif re.search(r"\bcompar",x): action=IntentAction.COMPARE
    elif re.search(
        r"\bcuanto (?:(?:sale|cuesta|esta)|(?:se )?esta cobrando|estan cobrando|se cobra)\b"
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
    if market==MarketScope.LOCAL and not g.province: reasons+=["MISSING_PROVINCE"]; question="¿En qué provincia se realiza el servicio?"
    if kind==EconomicObjectKind.UNKNOWN: reasons+=["UNKNOWN_ECONOMIC_OBJECT"]; question=question or "¿Qué servicio o producto tecnológico querés evaluar?"
    if p.currency=="UNKNOWN" and has_price: reasons+=["UNKNOWN_CURRENCY"]; question=question or "¿Ese monto está expresado en pesos argentinos o en otra moneda?"
    if kind==EconomicObjectKind.BUNDLE: reasons+=["BUNDLE_REQUIRES_COMPARABLE_SCOPE"]
    if re.search(r"\b(?:(?:cambio de )|(?:cambiar (?:un |una |el |la )?))(?:pantalla|teclado|fuente|ssd|disco)\b",x) and ps==PartsScope.UNKNOWN:
        reasons+=["UNKNOWN_PARTS_SCOPE"]; question=question or "¿El precio incluye el repuesto o es sólo mano de obra?"
    blocking={"MISSING_PROVINCE","UNKNOWN_ECONOMIC_OBJECT","UNKNOWN_CURRENCY","UNKNOWN_PARTS_SCOPE"}
    clar=bool(blocking & set(reasons)); conf=max(0.0,round(.95-(.25 if clar else 0)-(.15 if action==IntentAction.UNKNOWN else 0)-(.20 if kind==EconomicObjectKind.UNKNOWN else 0),2))
    return ParsedPricingQuery(raw_text,x,action,side,kind,sv,market,mod,p,g,dev,"USED" if re.search(r"\busad[oa]\b",x) else "NEW" if re.search(r"\bnuev[oa]\b",x) else "UNKNOWN",kind==EconomicObjectKind.BUNDLE,CommercialContext(parts_scope=ps),ParseMetadata(conf,clar,"|".join(reasons) if reasons else None,question,tuple(dict.fromkeys(explicit)),tuple(dict.fromkeys(inferred)),tuple(dict.fromkeys(derived))),language_evidence_type)
