from datetime import date
from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico


def test_oferta_debe_relacionar_empresa_con_servicio_canonico():
    empresa = Empresa(
        nombre="Proveedor X",
        provincia="Córdoba",
        ciudad="Córdoba",
        fuente="https://ejemplo.com/precios"
    )

    oferta = Oferta(
        empresa=empresa,
        servicio=ServicioCanonico.MALWARE,
        precio=15000,
        moneda="ARS",
        fecha_relevamiento=date(2026, 7, 30)
    )

    assert oferta.servicio == ServicioCanonico.MALWARE
    assert oferta.empresa.nombre == "Proveedor X"
    assert oferta.precio == 15000
    assert oferta.moneda == "ARS"