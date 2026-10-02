from dataclasses import replace
from datetime import date
from decimal import Decimal
import importlib
import pytest

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas


def observation(id, price="1299,50", **changes):
    module = importlib.import_module("src.dominio.market_observation")
    dto = OfertaDTO(empresa="Proveedor A", servicio="soporte tecnico", precio_raw=price,
                   provincia="Buenos Aires", ciudad="Villa de Mayo", moneda="ARS",
                   fuente="https://provider.example/tarifa", fecha_relevamiento=date(2026, 10, 2))
    item = module.MarketObservation(
        id=id, oferta=ProcesadorOfertas().procesar(dto), provider="Proveedor A",
        service="soporte_tecnico", currency="ARS", modality="remoto", unit="hora",
        scope="soporte general por hora", province="Buenos Aires", city="Villa de Mayo",
        source_url=dto.fuente, captured_at="2026-10-02T14:00:00+00:00",
        effective_date=None, capture_id="public", raw={"precio_raw":price},
        evidence_kind="public_capture", comparability_established=True,
    )
    return replace(item, **changes)


def query(items, **filters):
    module = importlib.import_module("src.aplicacion.market_query_service")
    return module.query_market(items, service="soporte_tecnico", **filters)


def test_benchmark_decimal_contadores_mediana_y_precio_propio():
    a = observation("a")
    b = observation("b", "1500,51", provider="Proveedor B")
    result = query([b, a], own_price="1399,50")
    group = result["benchmarks"][0]
    assert group["offer_count"] == 2
    assert group["provider_count"] == 2
    assert group["min"] == "1299.50"
    assert group["median"] == "1400.005"
    assert group["max"] == "1500.51"
    assert group["own_price_difference_pct"] == "-0.04"
    assert result == query([a, b], own_price="1399,50")


def test_no_mezcla_moneda_modalidad_periodo_scope_ni_servicio():
    a = observation("a")
    variants = [replace(a, id="usd", currency="USD"),
                replace(a, id="local", modality="local"),
                replace(a, id="mes", unit="mes"),
                replace(a, id="scope", scope="otra tarea"),
                replace(a, id="service", service="formateo")]
    result = query([a, *variants], own_price="1299,50", own_currency="ARS")
    assert len(result["benchmarks"]) == 5
    assert all(g["offer_count"] == 1 for g in result["benchmarks"])
    assert next(g for g in result["benchmarks"] if g["currency"] == "USD")["own_price_difference_pct"] is None


def test_exclusiones_explicitas_y_geografia_desconocida_no_se_inventa():
    a = observation("a")
    items = [a, replace(a,id="fixture", evidence_kind="illustrative"),
             replace(a,id="unknown",comparability_established=False),
             replace(a,id="modality",modality=None),
             replace(a,id="invalid",oferta=None),
             replace(a,id="geo",city=None,province=None)]
    result = query(items, province="Buenos Aires", city="Villa de Mayo")
    assert result["offer_count"] == 5
    assert result["benchmarks"][0]["offer_count"] == 1
    assert {o["exclusion_reason"] for o in result["offers"] if o["exclusion_reason"]} == {
        "Datos ilustrativos", "Comparabilidad no establecida", "Modalidad desconocida", "Precio inválido o servicio no normalizable"}
    assert query(items, province="Córdoba")["offers"] == []


def test_reimportaciones_no_inflan_proveedores_ni_ofertas_y_estado_vacio():
    a = observation("a")
    assert query([a,a])["benchmarks"][0]["offer_count"] == 1
    assert query([])["benchmarks"] == []
    assert query([])["unanswered"]


def test_hipotesis_citan_observaciones_sin_inferir_demanda():
    result = query([observation("a"),observation("b","2000,00",provider="B")])
    assert result["hypotheses"]
    assert result["hypotheses"][0]["evidence_ids"]
    assert result["limitations"]


def test_precio_propio_con_moneda_explicita_incompatible_no_se_compara():
    with pytest.raises(ValueError):
        query([observation("a")],own_price="USD 1300",own_currency="ARS")


def test_identidad_conflictiva_no_depende_del_orden_de_entrada():
    a=observation("a")
    b=observation("a","2000,00")
    with pytest.raises(ValueError): query([a,b])
