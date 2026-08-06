import re
from src.dominio.modelos.precio import Precio


class NormalizadorPrecios:

    @staticmethod
    def normalizar(valor_crudo: str) -> Precio:
        if not valor_crudo:
            return Precio(monto=0, moneda="ARS")

        texto = str(valor_crudo).upper()
        
        # Detección de moneda
        moneda = "USD" if "USD" in texto or "US$" in texto else "ARS"
        
        # Extraer únicamente los dígitos numéricos
        numeros = re.sub(r"[^\d]", "", texto)
        valor = int(numeros) if numeros else 0

        # Instanciar la entidad Precio con parámetros soportados
        return Precio(monto=valor, moneda=moneda)