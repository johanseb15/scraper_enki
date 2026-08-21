from src.aplicacion.language_query_contract import Geography
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.aplicacion.technical_need_market_resolution import (
    evaluate_pricing_readiness,
    resolve_technical_need_market,
    resolve_technical_route,
)


def test_os_installation_route_resolves_to_canonical_formateo_service():
    r=resolve_technical_route("OS_INSTALLATION_SERVICE")

    assert r.status=="RESOLVED"
    assert r.route=="OS_INSTALLATION_SERVICE"
    assert r.canonical_service=="FORMATEO_INSTALACION_SO"
    assert r.economic_object_kind=="SERVICE"
    assert r.market_scope=="LOCAL"


def test_hardware_diagnostic_route_does_not_resolve_to_repair_or_product():
    r=resolve_technical_route("HARDWARE_DIAGNOSTIC")

    assert r.status=="UNRESOLVED"
    assert r.canonical_service is None
    assert r.economic_object_kind is None
    assert r.market_scope is None
    assert "REPARACION_HARDWARE" not in (r.resolution_reason or "")


def test_windows_technical_need_keeps_routes_but_resolves_only_safe_market_objects():
    parsed=parse_pricing_query("Estoy instalando Windows 11 y se queda congelado en 10%. ¿Qué puede estar pasando?")

    result=resolve_technical_need_market(parsed.technical_need, geography=parsed.geography)

    assert parsed.technical_need.candidate_routes==(
        "DIAGNOSTIC_SERVICE",
        "OS_INSTALLATION_SERVICE",
        "HARDWARE_DIAGNOSTIC",
    )
    assert [r.route for r in result.resolutions]==[
        "DIAGNOSTIC_SERVICE",
        "OS_INSTALLATION_SERVICE",
        "HARDWARE_DIAGNOSTIC",
    ]
    resolved={r.route: r for r in result.resolutions if r.status=="RESOLVED"}
    unresolved={r.route: r for r in result.resolutions if r.status=="UNRESOLVED"}
    assert resolved["OS_INSTALLATION_SERVICE"].canonical_service=="FORMATEO_INSTALACION_SO"
    assert resolved["DIAGNOSTIC_SERVICE"].canonical_service=="DIAGNOSTICO_REVISION"
    assert unresolved["HARDWARE_DIAGNOSTIC"].canonical_service is None


def test_local_resolution_without_province_requires_geography_before_market():
    parsed=parse_pricing_query("Estoy instalando Windows 11 y se queda congelado en 10%. ¿Qué puede estar pasando?")

    result=resolve_technical_need_market(parsed.technical_need, geography=parsed.geography)

    assert result.clarification_required is True
    assert result.clarification_reason=="MISSING_PROVINCE_FOR_LOCAL_MARKET"
    assert all(
        r.market_status=="MISSING_PROVINCE"
        for r in result.resolutions
        if r.status=="RESOLVED" and r.market_scope=="LOCAL"
    )


def test_local_resolution_with_province_has_market_key_but_no_pricing_decision():
    parsed=parse_pricing_query("Estoy instalando Windows 11 y se queda congelado en 10%. ¿Qué puede estar pasando?")

    result=resolve_technical_need_market(parsed.technical_need, geography=Geography(province="Córdoba"))

    assert result.clarification_required is False
    resolved={r.route: r for r in result.resolutions if r.status=="RESOLVED"}
    assert resolved["OS_INSTALLATION_SERVICE"].market=="Córdoba"
    assert resolved["OS_INSTALLATION_SERVICE"].market_key=="Córdoba::FORMATEO_INSTALACION_SO"
    assert resolved["DIAGNOSTIC_SERVICE"].market_key=="Córdoba::DIAGNOSTICO_REVISION"



def test_windows_resolution_without_province_is_not_ready_for_pricing():
    parsed=parse_pricing_query("Estoy instalando Windows 11 y se queda congelado en 10%. ¿Qué puede estar pasando?")
    market_resolution=resolve_technical_need_market(parsed.technical_need, geography=parsed.geography)

    by_route={r.route: r for r in market_resolution.resolutions}
    readiness=evaluate_pricing_readiness(by_route["OS_INSTALLATION_SERVICE"])

    assert by_route["OS_INSTALLATION_SERVICE"].canonical_service=="FORMATEO_INSTALACION_SO"
    assert readiness.status=="MISSING_PROVINCE"
    assert readiness.ready is False
    assert readiness.canonical_service=="FORMATEO_INSTALACION_SO"
    assert readiness.market is None


def test_windows_resolution_with_province_is_ready_for_pricing_but_has_no_price_result():
    parsed=parse_pricing_query("Estoy instalando Windows 11 y se queda congelado en 10% en Córdoba. ¿Qué puede estar pasando?")
    market_resolution=resolve_technical_need_market(parsed.technical_need, geography=parsed.geography)

    by_route={r.route: r for r in market_resolution.resolutions}
    readiness=evaluate_pricing_readiness(by_route["OS_INSTALLATION_SERVICE"])

    assert readiness.status=="READY_FOR_PRICING"
    assert readiness.ready is True
    assert readiness.canonical_service=="FORMATEO_INSTALACION_SO"
    assert readiness.market=="Córdoba"
    assert readiness.market_key=="Córdoba::FORMATEO_INSTALACION_SO"
    assert readiness.pricing_status is None


def test_diagnostic_service_with_province_is_ready_for_pricing():
    parsed=parse_pricing_query("Estoy instalando Windows 11 y se queda congelado en 10% en Córdoba. ¿Qué puede estar pasando?")
    market_resolution=resolve_technical_need_market(parsed.technical_need, geography=parsed.geography)

    by_route={r.route: r for r in market_resolution.resolutions}
    readiness=evaluate_pricing_readiness(by_route["DIAGNOSTIC_SERVICE"])

    assert readiness.status=="READY_FOR_PRICING"
    assert readiness.ready is True
    assert readiness.canonical_service=="DIAGNOSTICO_REVISION"
    assert readiness.market_key=="Córdoba::DIAGNOSTICO_REVISION"


def test_hardware_diagnostic_readiness_is_unresolved_route_and_never_ready():
    r=resolve_technical_route("HARDWARE_DIAGNOSTIC")

    readiness=evaluate_pricing_readiness(r)

    assert readiness.status=="UNRESOLVED_ROUTE"
    assert readiness.ready is False
    assert readiness.canonical_service is None
    assert readiness.market_key is None
