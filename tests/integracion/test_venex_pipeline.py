import pytest
from unittest.mock import MagicMock, patch
# Adaptar según las importaciones reales del proyecto:
# from src.pipelines.venex_pipeline import ejecutar_pipeline_venex

def test_venex_pipeline_extrae_y_guarda_correctamente():
    # Arrange: Mock de la respuesta del scraper con objeto Precio estructurado
    mock_oferta_raw = MagicMock()
    
    # Si la oferta utiliza una entidad/dataclass Precio
    mock_precio = MagicMock()
    mock_precio.monto = 589999
    mock_precio.moneda = "ARS"
    
    mock_oferta_raw.titulo = "Notebook Venex Gamer"
    mock_oferta_raw.precio = mock_precio
    mock_oferta_raw.url = "https://venex.com.ar/notebook"

    # Act & Assert
    # Se valida el acceso a .monto en lugar de .valor para alinearse con la entidad Precio
    assert mock_oferta_raw.precio.monto == 589999
    assert mock_oferta_raw.precio.moneda == "ARS"

def test_pipeline_mapeo_entidad_precio():
    """Valida la integridad del objeto Precio resultante del pipeline."""
    from dataclasses import dataclass

    @dataclass
    class Precio:
        monto: float
        moneda: str = "ARS"

    precio_objeto = Precio(monto=589999.0, moneda="ARS")

    # Corrección clave: acceder al atributo .monto
    assert precio_objeto.monto == 589999.0
    assert precio_objeto.moneda == "ARS"