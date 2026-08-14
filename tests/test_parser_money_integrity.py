from src.aplicacion.language_query_contract import PriceType
from src.aplicacion.parser_consulta_pricing import parse_pricing_query

def test_argentine_dot_thousands_with_peso_symbol():
    r=parse_pricing_query("me quieren cobrar $60.000 por arreglar el Wi-Fi")
    assert r.price.currency=="ARS"
    assert r.price.type==PriceType.EXACT
    assert r.price.value==60000

def test_large_argentine_dot_thousands_with_peso_symbol():
    r=parse_pricing_query("me cotizaron $950.000 una PC para diseño gráfico")
    assert r.price.value==950000
    assert r.price.currency=="ARS"

def test_naked_argentine_dot_thousands():
    r=parse_pricing_query("me piden 150.000 por instalar 4 cámaras IP")
    assert r.price.value==150000
    assert r.price.currency=="UNKNOWN"

def test_multiple_argentine_thousands_groups():
    r=parse_pricing_query("1.200.000 por una notebook")
    assert r.price.value==1200000

def test_argentine_decimal_comma_is_preserved():
    r=parse_pricing_query("$85,00 por el servicio")
    assert r.price.value==85
    assert r.price.currency=="ARS"

def test_argentine_thousands_plus_decimal_comma():
    r=parse_pricing_query("$85.000,00 por el servicio")
    assert r.price.value==85000
    assert r.price.currency=="ARS"

def test_decimal_scalar_before_palos_still_means_millions():
    r=parse_pricing_query("1.2 palos por la notebook nueva con 32gb")
    assert r.price.value==1200000
    assert r.price.currency=="ARS"

def test_decimal_scalar_before_lucas_stays_scalar():
    r=parse_pricing_query("1.5 lucas por el cable")
    assert r.price.value==1500
    assert r.price.currency=="ARS"


def test_naked_multiple_groups_capture_full_token():
    r=parse_pricing_query("1.200.000 por una notebook")
    assert r.price.raw_expression=="1.200.000"
    assert r.price.value==1200000

def test_naked_two_group_thousands_still_work():
    r=parse_pricing_query("950.000 por una PC")
    assert r.price.raw_expression=="950.000"
    assert r.price.value==950000
