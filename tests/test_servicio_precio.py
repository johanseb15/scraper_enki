from dataclasses import dataclass
from datetime import date

from src.modelos.servicio_precio import ServicioPrecio

def test_crear_servicio_precio():
    servicio = ServicioPrecio(
        empresa="Vida Informática",
        provincia="Córdoba",
        ciudad="Córdoba",
        servicio="Eliminación de malware",
        equipo="PC",
        precio_freelance=29816,
        precio_local=41411,
        moneda="ARS",
        fecha_relevamiento=date(2024, 7, 14),
        fuente="https://vida-informatica.com.ar/precios",
    )

    assert servicio.empresa == "Vida Informática"
    assert servicio.servicio == "Eliminación de malware"
    assert servicio.precio_freelance == 29816
    assert servicio.precio_local == 41411
    assert servicio.moneda == "ARS"
