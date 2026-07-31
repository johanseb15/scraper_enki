import re
import unicodedata


class NormalizadorEmpresas:
    """
    Normaliza nombres de empresas para comparabilidad.
    """

    SUFIJOS_LEGALES = [
        r"\bS\.?\s*A\.?\s*S\.?\b",
        r"\bS\.?\s*R\.?\s*L\.?\b",
        r"\bS\.?\s*A\.?\b",
    ]

    def normalizar(self, nombre_crudo: str) -> str:
        if not nombre_crudo:
            return ""

        nombre = self._quitar_acentos(nombre_crudo)

        nombre = nombre.upper()

        for sufijo in self.SUFIJOS_LEGALES:
            nombre = re.sub(
                sufijo,
                "",
                nombre,
                flags=re.IGNORECASE
            )

        # Eliminar puntuación sobrante
        nombre = re.sub(
            r"[^\w\s]",
            "",
            nombre
        )

        # Normalizar espacios
        nombre = re.sub(
            r"\s+",
            " ",
            nombre
        )

        nombre = nombre.strip()

        return nombre.title()

    def _quitar_acentos(self, texto: str) -> str:
        normalizado = unicodedata.normalize(
            "NFD",
            texto
        )

        return "".join(
            caracter
            for caracter in normalizado
            if unicodedata.category(caracter) != "Mn"
        )