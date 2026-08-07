# src/modelos/precio.py

class Precio:
    def __init__(self, valor: float, moneda: str = "ARS", periodo: str = None):
        """
        Representa un valor monetario asociado a una oferta o servicio.
        
        Args:
            valor (float): La cantidad numérica del precio.
            moneda (str): El tipo de moneda (por defecto 'ARS').
            periodo (str, optional): Periodo de cobro (ej. mensual, único, hora).
        """
        self.valor = float(valor) if valor is not None else 0.0
        self.moneda = moneda
        self.periodo = periodo

    def __repr__(self) -> str:
        return f"Precio(valor={self.valor}, moneda='{self.moneda}', periodo='{self.periodo}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, Precio):
            return self.valor == other.valor and self.moneda == other.moneda and self.periodo == other.periodo
        return False