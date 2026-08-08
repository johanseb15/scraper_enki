"""Tests para el script orquestador de ingesta masiva scripts.ingestar_todo."""

import inspect
from unittest.mock import MagicMock, patch
import pytest
from src.scrapers.compragamer_scraper import OfertaDTO


def test_ejecutar_ingesta_exitoso(tmp_path):
    db_test = str(tmp_path / "test.db")

    sig = inspect.signature(OfertaDTO.__init__)
    params = [p for p in sig.parameters.keys() if p != "self"]

    kwargs = {}
    for p in params:
        if "precio" in p:
            kwargs[p] = 12000.0
        elif "moneda" in p:
            kwargs[p] = "ARS"
        elif "url" in p:
            kwargs[p] = "https://compragamer.com/item001"
        elif "proveedor" in p:
            kwargs[p] = "CompraGamer"
        else:
            kwargs[p] = "Mantenimiento preventivo PC"

    oferta_mock = OfertaDTO(**kwargs)

    with patch(
        "src.infraestructura.scrapers.compragamer_playwright_scraper.CompraGamerPlaywrightScraper.obtener_ofertas",
        return_value=[oferta_mock, "Oferta en string puro"],
    ), patch(
        "src.infraestructura.sqlite.repositorio_sqlite_ofertas.RepositorioSQLiteOfertas"
    ) as mock_repo_cls:
        mock_repo_instance = MagicMock()
        mock_repo_cls.return_value = mock_repo_instance

        from scripts.ingestar_todo import ejecutar_ingesta

        total = ejecutar_ingesta(db_path=db_test)

        assert total == 2
        mock_repo_cls.assert_called_once_with(db_test)
        assert mock_repo_instance.guardar.call_count == 2
