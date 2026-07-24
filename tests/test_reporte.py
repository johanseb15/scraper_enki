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