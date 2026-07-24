from datetime import date

from src.modelos.servicio_precio import ServicioPrecio
from src.reporte import generar_resumen_servicio

def test_generar_resumen_compara_servicios_con_nombres_equivalentes():
    servicios = [
        ServicioPrecio(
            empresa="Vida Informatica",
            provincia="Cordoba",
            ciudad="Cordoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=29816,
            precio_local=41411,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="",
        ),
        ServicioPrecio(
            empresa="BairesCloud",
            provincia="Buenos Aires",
            ciudad="Buenos Aires",
            servicio="Eliminación de malware / spyware",
            equipo="PC",
            precio_freelance=25000,
            precio_local=25000,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="",
        ),
    ]

    resumen = generar_resumen_servicio(
        servicios,
        "Eliminación de malware",
    )

    assert resumen["empresas_relevadas"] == 2


def test_generar_resumen_compara_servicios_sin_diferenciar_mayusculas_acentos():
    servicios = [
        ServicioPrecio(
            empresa="Vida Informatica",
            provincia="Cordoba",
            ciudad="Cordoba",
            servicio="Eliminación de Malware",
            equipo="PC",
            precio_freelance=29816,
            precio_local=41411,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="",
        ),
        ServicioPrecio(
            empresa="BairesCloud",
            provincia="Buenos Aires",
            ciudad="Buenos Aires",
            servicio="eliminacion de malware / spyware",
            equipo="PC",
            precio_freelance=25000,
            precio_local=25000,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="",
        ),
    ]

    resumen = generar_resumen_servicio(
        servicios,
        "eliminación de malware",
    )

    assert resumen["empresas_relevadas"] == 2


def test_generar_resumen_compara_precios_entre_empresas():
    servicios = [
        ServicioPrecio(
            empresa="Vida Informatica",
            provincia="Cordoba",
            ciudad="Cordoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=29816,
            precio_local=41411,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="",
        ),
        ServicioPrecio(
            empresa="BairesCloud",
            provincia="Buenos Aires",
            ciudad="Buenos Aires",
            servicio="Eliminación de malware / spyware",
            equipo="PC",
            precio_freelance=25000,
            precio_local=25000,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="",
        ),
    ]

    resumen = generar_resumen_servicio(
        servicios,
        "Eliminación de malware",
    )

    assert resumen["precio_minimo"] == 25000
    assert resumen["precio_maximo"] == 29816
    assert resumen["precio_promedio"] == 27408

def test_generar_resumen_servicio_sin_datos_devuelve_resumen_vacio():
    resumen = generar_resumen_servicio(
        [],
        "Eliminación de malware",
    )

    assert resumen["cantidad"] == 0
    assert resumen["empresas_relevadas"] == 0
    assert resumen["precio_minimo"] is None
    assert resumen["precio_promedio"] is None
    assert resumen["precio_maximo"] is None


def test_generar_resumen_incluye_precios_por_empresa():
    servicios = [
        ServicioPrecio(
            empresa="Vida Informatica",
            provincia="Cordoba",
            ciudad="Cordoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=29816,
            precio_local=41411,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="",
        ),
        ServicioPrecio(
            empresa="BairesCloud",
            provincia="Buenos Aires",
            ciudad="Buenos Aires",
            servicio="Eliminación de malware / spyware",
            equipo="PC",
            precio_freelance=25000,
            precio_local=25000,
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
            fuente="",
        ),
    ]

    resumen = generar_resumen_servicio(
        servicios,
        "Eliminación de malware",
    )

    assert resumen["precios_por_empresa"] == {
        "Vida Informatica": 29816,
        "BairesCloud": 25000,
    }