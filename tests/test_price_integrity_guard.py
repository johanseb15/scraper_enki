from datetime import date

import pytest

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.oferta_factory import OfertaFactory
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.normalizadores.normalizador_precios import NormalizadorPrecios


def _dto(precio_raw, precio=None):
    return OfertaDTO(
        empresa_nombre="Empresa de prueba",
        provincia="Córdoba",
        ciudad="Córdoba",
        fuente="https://fuente.example/precios",
        servicio_raw="Formateo e instalación de SO",
        precio=precio,
        precio_raw=precio_raw,
        moneda="ARS",
        fecha_relevamiento=date(2026, 8, 9),
    )


def test_precio_exacto_sigue_siendo_representable():
    precio = NormalizadorPrecios.normalizar("$35.000")

    assert precio is not None
    assert precio.valor == 35000
    assert precio.moneda == "ARS"


@pytest.mark.parametrize(
    "precio_raw",
    [
        "Desde $35.000",
        "$35.000–$60.000",
        "Consultar",
        "$45",
    ],
)
def test_normalizador_no_convierte_semantica_no_representable_en_precio_exacto(
    precio_raw,
):
    assert NormalizadorPrecios.normalizar(precio_raw) is None


def test_ausencia_y_cero_literal_siguen_siendo_distinguibles():
    assert NormalizadorPrecios.normalizar("") is None
    assert NormalizadorPrecios.normalizar(None) is None

    cero_literal = NormalizadorPrecios.normalizar("$0")
    assert cero_literal is not None
    assert cero_literal.valor == 0


@pytest.mark.parametrize(
    ("precio_raw", "codigo"),
    [
        ("Desde $35.000", "PRECIO_NO_REPRESENTABLE"),
        ("$35.000–$60.000", "PRECIO_NO_REPRESENTABLE"),
        ("Consultar", "PRECIO_NO_REPRESENTABLE"),
        ("$45", "PRECIO_AMBIGUO"),
        ("", "PRECIO_AUSENTE"),
        (None, "PRECIO_AUSENTE"),
        ("$0", "PRECIO_CERO_LITERAL"),
    ],
)
def test_camino_plural_rechaza_precio_sin_persistirlo(
    tmp_path, precio_raw, codigo
):
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "price_guard.db")
    )
    procesador = ProcesadorOfertas(repositorio=repositorio)

    ofertas = procesador.crear_ofertas(_dto(precio_raw))

    assert ofertas == []
    assert repositorio.obtener_todas() == []
    assert len(procesador.rechazos) == 1
    assert codigo in procesador.rechazos[0].razon
    assert procesador.rechazos[0].fuente == "https://fuente.example/precios"


def test_camino_singular_rechaza_rango_de_forma_trazable(tmp_path):
    repositorio = RepositorioSQLiteOfertas(
        ruta_db=str(tmp_path / "price_guard_singular.db")
    )
    procesador = ProcesadorOfertas(repositorio=repositorio)

    oferta = procesador.crear_oferta(_dto("$35.000–$60.000"))

    assert oferta is None
    assert repositorio.obtener_todas() == []
    assert "PRECIO_NO_REPRESENTABLE" in procesador.rechazos[0].razon


def test_precio_preinterpretado_no_oculta_raw_no_representable():
    procesador = ProcesadorOfertas()

    ofertas = procesador.crear_ofertas(_dto("Desde $35.000", precio=35000))

    assert ofertas == []
    assert "PRECIO_NO_REPRESENTABLE" in procesador.rechazos[0].razon


def test_factory_no_crea_oferta_desde_raw_no_representable():
    oferta = OfertaFactory().crear_desde_dto(
        _dto("$35.000–$60.000", precio=3500060000)
    )

    assert oferta is None
