from decimal import Decimal
import sqlite3
import pytest

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas
from src.estadisticas import calcular_precio_minimo


def test_pipeline_persiste_centavos_exactos_y_unknown(tmp_path):
    repo = RepositorioSQLiteOfertas(tmp_path / "money.db")
    original = ProcesadorOfertas(repositorio=repo).procesar(OfertaDTO(
        empresa="Proveedor", servicio="formateo", precio_raw="$1.299,50",
        fuente="https://proveedor.example/tarifa", provincia="", ciudad="",
    ))
    recovered = repo.obtener_todas()[0]
    assert recovered.precio.valor == Decimal("1299.50")
    assert isinstance(recovered.precio.valor, Decimal)
    assert recovered.precio_raw == "$1.299,50"
    assert recovered.fecha_relevamiento is None
    assert recovered.modalidad is None
    assert calcular_precio_minimo([recovered]) == Decimal("1299.50")


def test_persistencia_no_redondea_importes_grandes(tmp_path):
    repo = RepositorioSQLiteOfertas(tmp_path / "big.db")
    ProcesadorOfertas(repositorio=repo).procesar(OfertaDTO(
        empresa="Proveedor", servicio="formateo", precio_raw="$99.999.999.999.999,99",
    ))
    assert repo.obtener_todas()[0].precio.valor == Decimal("99999999999999.99")


def test_texto_original_es_autoridad_si_scraper_trunco_centavos():
    oferta = ProcesadorOfertas().procesar(OfertaDTO(
        empresa="Proveedor", servicio="formateo", precio=1299, precio_raw="$1.299,50"))
    assert oferta.precio.valor == Decimal("1299.50")
    assert oferta.precio.raw == "$1.299,50"


@pytest.mark.parametrize("raw",["1.2.3,50","12.34.56","1,23,456","1..299","1.299,5000"])
def test_separadores_malformados_no_se_convierten_en_precio(raw):
    from src.normalizadores.normalizador_precios import NormalizadorPrecios
    assert NormalizadorPrecios.normalizar(raw) is None


def test_identidad_sqlite_no_colapsa_centavos_sin_texto_raw(tmp_path):
    repo = RepositorioSQLiteOfertas(tmp_path / "identidad.db")
    processor=ProcesadorOfertas(repositorio=repo)
    for price in ("99999999999999.99","99999999999999.98"):
        processor.procesar(OfertaDTO(empresa="Proveedor",servicio="formateo",precio=Decimal(price)))
    assert {o.precio.valor for o in repo.obtener_todas()} == {Decimal("99999999999999.99"),Decimal("99999999999999.98")}


def test_dto_y_pipeline_conservan_modalidad_declarada(tmp_path):
    repo=RepositorioSQLiteOfertas(tmp_path / "modalidad.db")
    try:
        dto=OfertaDTO(empresa="Proveedor",servicio="soporte tecnico",precio_raw="1300,50",modalidad="remoto")
    except TypeError:
        pytest.fail("El DTO todavía no transporta modalidad declarada")
    ProcesadorOfertas(repositorio=repo).procesar(dto)
    assert repo.obtener_todas()[0].modalidad == "remoto"


def test_identidad_sin_raw_no_depende_de_escala_decimal(tmp_path):
    repo=RepositorioSQLiteOfertas(tmp_path / "escala.db")
    processor=ProcesadorOfertas(repositorio=repo)
    for price in ("1300.5","1300.50"):
        processor.procesar(OfertaDTO(empresa="Proveedor",servicio="formateo",precio=Decimal(price)))
    assert len(repo.obtener_todas()) == 1
