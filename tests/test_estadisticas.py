from datetime import date

import pytest

from src.estadisticas import (
    calcular_precio_promedio,
    calcular_precio_minimo,
    calcular_precio_maximo,
)
from src.modelos.servicio_precio import ServicioPrecio


def test_calcula_precio_promedio_de_un_servicio():
    datos = [
        ServicioPrecio(
            empresa="A",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=30000,
            precio_local=40000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="a.com",
        ),
        ServicioPrecio(
            empresa="B",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=32000,
            precio_local=42000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="b.com",
        ),
        ServicioPrecio(
            empresa="C",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=34000,
            precio_local=44000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="c.com",
        ),
    ]

    promedio = calcular_precio_promedio(
        datos,
        servicio="Eliminación de malware",
    )

    assert promedio == 32000


def test_calcula_precio_minimo_de_un_servicio():
    datos = [
        ServicioPrecio(
            empresa="A",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=30000,
            precio_local=40000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="a.com",
        ),
        ServicioPrecio(
            empresa="B",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=28000,
            precio_local=39000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="b.com",
        ),
        ServicioPrecio(
            empresa="C",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=34000,
            precio_local=44000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="c.com",
        ),
    ]

    minimo = calcular_precio_minimo(
        datos,
        servicio="Eliminación de malware",
    )

    assert minimo == 28000


def test_calcula_precio_maximo_de_un_servicio():
    datos = [
        ServicioPrecio(
            empresa="A",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=30000,
            precio_local=40000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="a.com",
        ),
        ServicioPrecio(
            empresa="B",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=28000,
            precio_local=39000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="b.com",
        ),
        ServicioPrecio(
            empresa="C",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Eliminación de malware",
            equipo="PC",
            precio_freelance=34000,
            precio_local=44000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="c.com",
        ),
    ]

    maximo = calcular_precio_maximo(
        datos,
        servicio="Eliminación de malware",
    )

    assert maximo == 34000


def test_precio_promedio_servicio_inexistente_da_error_claro():
    datos = [
        ServicioPrecio(
            empresa="A",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Formateo",
            equipo="PC",
            precio_freelance=25000,
            precio_local=35000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="a.com",
        ),
    ]

    with pytest.raises(ValueError, match="sin datos relevados"):
        calcular_precio_promedio(
            datos,
            "Eliminación de malware",
        )


def test_precio_minimo_servicio_inexistente_da_error_claro():
    datos = [
        ServicioPrecio(
            empresa="A",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Formateo",
            equipo="PC",
            precio_freelance=25000,
            precio_local=35000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="a.com",
        ),
    ]

    with pytest.raises(ValueError, match="sin datos relevados"):
        calcular_precio_minimo(
            datos,
            "Eliminación de malware",
        )


def test_precio_maximo_servicio_inexistente_da_error_claro():
    datos = [
        ServicioPrecio(
            empresa="A",
            provincia="Córdoba",
            ciudad="Córdoba",
            servicio="Formateo",
            equipo="PC",
            precio_freelance=25000,
            precio_local=35000,
            moneda="ARS",
            fecha_relevamiento=date(2024, 7, 14),
            fuente="a.com",
        ),
    ]

    with pytest.raises(ValueError, match="sin datos relevados"):
        calcular_precio_maximo(
            datos,
            "Eliminación de malware",
        )
