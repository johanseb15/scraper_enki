from src.aplicacion.language_query_contract import EconomicObjectKind,IntentAction,IntentSide,MarketScope,PartsScope,QueryKind,ServiceModality
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_evaluate_buy_local():
    r=parse_pricing_query("me quieren cobrar 80 lucas por formatear la notebook en Córdoba, está bien?")
    assert r.intent_action==IntentAction.EVALUATE_PRICE and r.intent_side==IntentSide.BUY
    assert r.price.value==80000 and r.price.currency=="ARS" and r.geography.province=="Córdoba"
    assert "FORMATEO_INSTALACION_SO" in r.canonical_services and r.market_scope==MarketScope.LOCAL
def test_sell_suggest_remote():
    r=parse_pricing_query("cuánto debería cobrar por soporte remoto?")
    assert r.intent_action==IntentAction.SUGGEST_PRICE and r.intent_side==IntentSide.SELL
    assert r.market_scope==MarketScope.REMOTE_NATIONAL and not r.metadata.clarification_required
def test_remote_evaluate():
    r=parse_pricing_query("quiero cobrar 35 lucas por soporte remoto, está bien?")
    assert r.price.value==35000 and r.modality==ServiceModality.REMOTE
def test_lucas_k_palo():
    assert parse_pricing_query("45 lucas por diagnóstico en CABA").price.value==45000
    assert parse_pricing_query("45k por diagnóstico en CABA").price.value==45000
    assert parse_pricing_query("un palo por una pc usada").price.value==1000000
def test_approximate():
    r=parse_pricing_query("casi 100 lucas por formatear en CABA")
    assert r.price.value==100000 and r.price.is_approximate
def test_naked_number_currency_unknown():
    r=parse_pricing_query("80 por formatear en Córdoba está bien?")
    assert r.price.value==80 and r.price.currency=="UNKNOWN" and r.metadata.clarification_required
def test_city_to_province():
    r=parse_pricing_query("cuánto sale el formateo en Rosario?")
    assert r.geography.city=="Rosario" and r.geography.province=="Santa Fe"
    assert "geography.province" in r.metadata.inferred_fields
def test_missing_province():
    r=parse_pricing_query("cuánto sale formatear una notebook?")
    assert r.market_scope==MarketScope.LOCAL and r.metadata.clarification_required
def test_bundle_preserved():
    r=parse_pricing_query("me cobran 110 lucas por formateo y backup en Córdoba")
    assert r.economic_object_kind==EconomicObjectKind.BUNDLE and r.is_bundle
    assert "FORMATEO_INSTALACION_SO" in r.canonical_services and "BACKUP_DATOS" in r.canonical_services
def test_backup_not_recovery():
    r=parse_pricing_query("formateo con respaldo en Córdoba")
    assert "BACKUP_DATOS" in r.canonical_services and "RECUPERACION_DATOS" not in r.canonical_services
def test_parts_scope():
    r=parse_pricing_query("me cobran 50 lucas solo mano de obra por cambio de pantalla en CABA")
    assert r.commercial_context.parts_scope==PartsScope.LABOR_ONLY
def test_unknown_parts_scope():
    r=parse_pricing_query("me cobran 95 lucas por cambio de pantalla en CABA")
    assert r.metadata.clarification_required and "UNKNOWN_PARTS_SCOPE" in r.metadata.clarification_reason
def test_hardware_goods():
    r=parse_pricing_query("cuánto sale una RTX 4060 nueva?")
    assert r.economic_object_kind==EconomicObjectKind.HARDWARE and r.market_scope==MarketScope.GOODS and r.condition=="NEW"
def test_used_hardware():
    assert parse_pricing_query("un palo por una pc usada").condition=="USED"
def test_onsite_only_explicit():
    assert parse_pricing_query("cuánto sale formatear en Córdoba?").modality==ServiceModality.UNKNOWN
    assert parse_pricing_query("cuánto sale formatear a domicilio en Córdoba?").modality==ServiceModality.ONSITE
def test_workshop_explicit():
    assert parse_pricing_query("cuánto sale formatear en taller en Córdoba?").modality==ServiceModality.WORKSHOP
def test_range():
    r=parse_pricing_query("entre 60 y 80 lucas por diagnóstico en Córdoba")
    assert r.price.min==60000 and r.price.max==80000
def test_per_hour():
    assert parse_pricing_query("35 lucas por hora de soporte remoto").price.type.value=="PER_HOUR"
def test_provenance():
    assert parse_pricing_query("me cobran 40 lucas por formatear en CABA",language_evidence_type="SYNTHETIC_GROK").language_evidence_type=="SYNTHETIC_GROK"
def test_service_word_ambiguous():
    r=parse_pricing_query("cuánto sale el service en CABA?")
    assert r.economic_object_kind==EconomicObjectKind.UNKNOWN and r.metadata.clarification_required

def test_windows_installation_failure_is_technical_need_not_pricing():
    r=parse_pricing_query("Estoy instalando Windows 11 y se queda congelado en 10%. ¿Qué puede estar pasando?")
    assert r.query_kind==QueryKind.TECHNICAL_NEED
    assert r.technical_need is not None
    assert r.technical_need.domain=="PC"
    assert r.technical_need.technical_problem=="OS_INSTALLATION_FAILURE"
    assert r.technical_need.economic_intent_explicit is False
    assert r.technical_need.candidate_routes==(
        "DIAGNOSTIC_SERVICE",
        "OS_INSTALLATION_SERVICE",
        "HARDWARE_DIAGNOSTIC",
    )
    assert r.technical_need.product_purchase_recommendation=="NONE_YET"
    assert r.technical_need.clarification_required is True
    assert r.price.value is None
