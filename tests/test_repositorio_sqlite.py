from datetime import date
from pathlib import Path

from src.modelos.servicio_precio import ServicioPrecio
from src.repositorio import RepositorioSQLite
from src.scrapers.baires_cloud import extraer_precios_bairescloud


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


def test_bairescloud_puede_guardarse_en_sqlite():
    html = Path(
        "tests/fixtures/bairescloud.html"
    ).read_text(encoding="utf-8")

    servicios = extraer_precios_bairescloud(
        html=html,
        fecha_relevamiento=date(2026, 2, 1),
    )

    repositorio = RepositorioSQLite(":memory:")

    for servicio in servicios:
        repositorio.guardar(servicio)

    resultados = repositorio.obtener_todos()

    assert len(resultados) == len(servicios)
    assert len(resultados) > 0
    assert resultados[0].empresa == "BairesCloud"
