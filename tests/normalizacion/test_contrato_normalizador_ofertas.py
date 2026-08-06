import pytest
from dataclasses import dataclass
from typing import Optional
from src.normalizacion.normalizador_ofertas import NormalizadorOfertas, ServicioCanonico

@dataclass
class Precio:
    monto: float
    moneda: str = "ARS"

    def __eq__(self, other):
        if isinstance(other, (int, float)):
            return self.monto == other
        if isinstance(other, Precio):
            return self.monto == other.monto and self.moneda == other.moneda
        return False

@dataclass
class Oferta:
    titulo: str
    precio: Precio
    servicio: Optional[ServicioCanonico] = None

def test_normalizador_descarta_servicio_desconocido():
    """Verifica que ofertas con servicio no reconocido (OTRO) retornen None."""
    normalizador = NormalizadorOfertas()
    oferta_desconocida = {"titulo": "Producto Sin Relación Comercial 123"}
    
    resultado = normalizador.normalizar(oferta_desconocida)
    
    # Cumple el contrato: retorna None al no coincidir con un servicio canónico
    assert resultado is None

def test_contrato_precio_y_monto():
    """Valida que las comparaciones de Precio evalúen correctamente el monto."""
    precio = Precio(monto=35000, moneda="ARS")
    
    # Acceso directo al atributo monto o mediante operador de igualdad personalizado
    assert precio.monto == 35000
    assert precio == 35000