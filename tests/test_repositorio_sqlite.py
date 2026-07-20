from datetime import date

from src.modelos.servicio_precio import ServicioPrecio
from src.repositorio import RepositorioSQLite


def test_guardar_y_recuperar_servicio():

    repositorio = RepositorioSQLite(":memory:")

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

    repositorio.guardar(servicio)

    resultados = repositorio.obtener_todos()

    assert len(resultados) == 1
    assert resultados[0] == servicio

def test_guardar_dos_veces_el_mismo_servicio_no_lo_duplica():
    repositorio = RepositorioSQLite(":memory:")

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

    repositorio.guardar(servicio)
    repositorio.guardar(servicio)  

    resultados = repositorio.obtener_todos()

    assert len(resultados) == 1

