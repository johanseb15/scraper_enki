from datetime import date

import pytest

from src.api.main import app, obtener_repositorio
from src.dominio.empresa import Empresa
from src.dominio.oferta import Oferta
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)


@pytest.fixture
def mercado_api(tmp_path):
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "mercado_api.db")
    )
    ofertas = [
        Oferta(
            empresa=Empresa(
                nombre="Vida informatica",
                provincia="Córdoba",
                ciudad="Córdoba",
                fuente="test",
            ),
            servicio=ServicioCanonico.MALWARE,
            servicio_raw="Eliminación de malware",
            precio=29816,
            modalidad="local",
            precio_raw="$ 29.816",
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
        ),
        Oferta(
            empresa=Empresa(
                nombre="BairesCloud",
                provincia="Buenos Aires",
                ciudad="Buenos Aires",
                fuente="test",
            ),
            servicio=ServicioCanonico.MALWARE,
            servicio_raw="Eliminación de malware",
            precio=46000,
            modalidad="local",
            precio_raw="$ 46.000",
            moneda="ARS",
            fecha_relevamiento=date(2026, 7, 20),
        ),
    ]
    for oferta in ofertas:
        repositorio.guardar(oferta)

    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    try:
        yield repositorio
    finally:
        app.dependency_overrides.pop(obtener_repositorio, None)
