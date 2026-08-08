import re

from src.dominio.oferta import PrecioValor


class NormalizadorPrecios:
    @staticmethod
    def normalizar(valor_crudo: str) -> PrecioValor:
        if not valor_crudo:
            return PrecioValor(valor=0, moneda="ARS")

        texto = str(valor_crudo).upper()
        moneda = "USD" if "USD" in texto or "US$" in texto else "ARS"
        numeros = re.sub(r"[^\d]", "", texto)
        valor = int(numeros) if numeros else 0
        periodo = "mensual" if "MES" in texto else None

        return PrecioValor(valor=valor, moneda=moneda, periodo=periodo)
