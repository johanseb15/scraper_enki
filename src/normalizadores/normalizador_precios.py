import re

from src.dominio.oferta import PrecioValor


class NormalizadorPrecios:
    _PATRON_EXACTO = re.compile(
        r"^\s*(?:(?:AR\$|ARS|US\$|USD|U\$S|\$)\s*)?"
        r"\d+(?:[.,]\d+)*"
        r"\s*(?:(?:ARS|USD))?"
        r"(?:\s*(?:/|X)\s*MES)?\s*$",
        re.IGNORECASE,
    )
    _PATRON_ABREVIADO_AMBIGUO = re.compile(
        r"^\s*\$\s*\d{1,3}(?:\s*[\-–]\s*\d{1,3}K)?\s*$",
        re.IGNORECASE,
    )

    @classmethod
    def motivo_rechazo(cls, valor_crudo: str | None) -> str | None:
        if valor_crudo is None or not str(valor_crudo).strip():
            return "PRECIO_AUSENTE"

        texto = str(valor_crudo).strip().upper()
        if cls._PATRON_ABREVIADO_AMBIGUO.fullmatch(texto):
            if int(re.sub(r"[^\d]", "", texto) or 0) == 0:
                return "PRECIO_CERO_LITERAL"
            return "PRECIO_AMBIGUO"

        if not cls._PATRON_EXACTO.fullmatch(texto):
            return "PRECIO_NO_REPRESENTABLE"

        numeros = re.sub(r"[^\d]", "", texto)
        if int(numeros or 0) == 0:
            return "PRECIO_CERO_LITERAL"

        return None

    @classmethod
    def normalizar(cls, valor_crudo: str | None) -> PrecioValor | None:
        motivo = cls.motivo_rechazo(valor_crudo)
        if motivo and motivo != "PRECIO_CERO_LITERAL":
            return None

        texto = str(valor_crudo).upper()
        moneda = "USD" if "USD" in texto or "US$" in texto else "ARS"
        numeros = re.sub(r"[^\d]", "", texto)
        valor = int(numeros) if numeros else 0
        periodo = "mensual" if "MES" in texto else None

        return PrecioValor(valor=valor, moneda=moneda, periodo=periodo)
