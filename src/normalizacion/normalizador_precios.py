import re

from src.modelos.precio import Precio


class NormalizadorPrecios:

    @staticmethod
    def normalizar(valor_crudo: str) -> Precio:
        texto = valor_crudo.upper()

        moneda = "ARS"

        if "USD" in texto:
            moneda = "USD"

        numeros = re.sub(r"[^\d]", "", texto)

        valor = int(numeros)

        periodo = None

        if "MES" in texto:
            periodo = "mensual"

        return Precio(
            valor=valor,
            moneda=moneda,
            periodo=periodo,
        )