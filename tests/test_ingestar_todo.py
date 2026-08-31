"""Tests para el entrypoint de ingesta masiva scripts.ingestar_todo."""

from datetime import date

from scripts.ingestar_todo import ejecutar_ingesta
from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.dominio.oferta import Oferta
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.infraestructura.scrapers.base import BaseScraper


class ScraperCompraGamerFixture(BaseScraper):
    def obtener_servicios(self) -> list[OfertaDTO]:
        fecha = date(2026, 8, 8)
        return [
            OfertaDTO(
                empresa_nombre="Compra Gamer",
                provincia="Buenos Aires",
                ciudad="CABA",
                servicio_raw="Mantenimiento preventivo",
                precio=12000,
                precio_raw="$ 12.000",
                moneda="ARS",
                fuente="https://compragamer.com/item001",
                fecha_relevamiento=fecha,
            ),
            OfertaDTO(
                empresa_nombre="Compra Gamer",
                provincia="Buenos Aires",
                ciudad="CABA",
                servicio_raw="Soporte técnico informático",
                precio=18000,
                precio_raw="$ 18.000",
                moneda="ARS",
                fuente="https://compragamer.com/item002",
                fecha_relevamiento=fecha,
            ),
        ]


def test_ejecutar_ingesta_exitoso(tmp_path):
    db_test = str(tmp_path / "test.db")

    total = ejecutar_ingesta(
        db_path=db_test,
        scrapers=[ScraperCompraGamerFixture()],
    )

    persistidas = RepositorioSQLiteOfertas(ruta_db=db_test).obtener_todas()
    assert total == 2
    assert len(persistidas) == 2
    assert all(isinstance(oferta, Oferta) for oferta in persistidas)
    assert {oferta.empresa.nombre for oferta in persistidas} == {"Compra Gamer"}
    assert {oferta.precio.valor for oferta in persistidas} == {12000, 18000}
