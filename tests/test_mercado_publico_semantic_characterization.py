from src.aplicacion.caracterizador_mercado_publico import (
    clasificar_scope_tecnologico,
    explicar_consistencia_linea,
    explicar_consistencia_orden,
)


def test_codigo_unspsc_8111_es_tech_relevant_por_servicios_informaticos():
    result = clasificar_scope_tecnologico("81111800", "Servicios inform?ticos / Administraci?n de sistemas")

    assert result.status == "TECH_RELEVANT"
    assert result.reason == "UNSPSC_8111_COMPUTER_SERVICES"


def test_codigo_unspsc_43_es_tech_relevant_por_segmento_ti():
    result = clasificar_scope_tecnologico("43211500", "Equipos inform?ticos")

    assert result.status == "TECH_RELEVANT"
    assert result.reason == "UNSPSC_43_IT_BROADCAST_TELECOM"


def test_categoria_no_tecnologica_con_codigo_oficial_es_non_tech():
    result = clasificar_scope_tecnologico("42242000", "Equipamiento y suministros m?dicos")

    assert result.status == "NON_TECH"
    assert result.reason == "UNSPSC_STRUCTURED_NON_TECH"


def test_codigo_cero_o_desconocido_es_unknown():
    result = clasificar_scope_tecnologico("0", "UNKNOWN")

    assert result.status == "UNKNOWN"
    assert result.reason == "MISSING_OR_UNKNOWN_OFFICIAL_CLASSIFICATION"


def test_line_total_cero_explica_mismatch_sin_corregir_valor():
    result = explicar_consistencia_linea(quantity=2.0, net_price=35000.0, line_total=0.0)

    assert result.status == "MISMATCH"
    assert result.reason == "LINE_TOTAL_ZERO_BUT_QUANTITY_X_NET_PRICE_POSITIVE"
    assert result.expected_quantity_x_net_price == 70000.0
    assert result.observed_total == 0.0


def test_order_total_se_explica_por_header_neto_impuestos_cargos_descuentos():
    result = explicar_consistencia_orden(
        order_total=210630.0,
        total_neto=177000.0,
        impuestos=33630.0,
        cargos=0.0,
        descuentos=0.0,
        sum_line_total=0.0,
    )

    assert result.status == "MISMATCH"
    assert result.reason == "ORDER_TOTAL_MATCHES_HEADER_NET_TAX_CHARGES_DISCOUNTS_NOT_LINE_TOTALS"
    assert result.expected_header_total == 210630.0
