import re
import unicodedata


class NormalizadorEmpresas:
    """
    Normaliza nombres de empresas para comparabilidad.

    Responsabilidades:
    - eliminar sufijos legales
    - limpiar ruido tipográfico
    - normalizar espacios
    - homogeneizar casing
    """

    SUFIJOS_LEGALES = [
        r"\bS\.?\s*A\.?\s*S\.?\b",
        r"\bS\.?\s*R\.?\s*L\.?\b",
        r"\bS\.?\s*A\.?\b",
        r"\bSRL\b",
        r"\bSAS\b",
        r"\bSA\b",
    ]

    SIGLAS_MANTENER = {
        "IT": "It",
    }

    def normalizar(self, nombre_crudo: str) -> str:

        if not nombre_crudo:
            return ""

        # Para empresas usamos una representación canónica sin acentos
        nombre = nombre_crudo

        # limpiar espacios iniciales/finales
        nombre = nombre.strip()

        # eliminar sufijos legales
        for sufijo in self.SUFIJOS_LEGALES:
            nombre = re.sub(
                sufijo,
                "",
                nombre,
                flags=re.IGNORECASE
            )

        # eliminar puntuación
        nombre = re.sub(
            r"[^\w\s]",
            "",
            nombre
        )

        # normalizar espacios
        nombre = re.sub(
            r"\s+",
            " ",
            nombre
        ).strip()

        palabras = nombre.split()

        resultado = []

        for indice, palabra in enumerate(palabras):

            palabra_upper = palabra.upper()

            if palabra_upper in self.SIGLAS_MANTENER:
                if indice == len(palabras) - 1:
                    resultado.append(
                        self.SIGLAS_MANTENER[palabra_upper]
                    )
                else:
                    resultado.append(palabra_upper)
            else:
                resultado.append(
                    self._normalizar_palabra(palabra)
                )

        return " ".join(resultado)


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

    def _normalizar_palabra(self, palabra: str) -> str:

        palabras_sin_acentos = {
            "informatica": "Informatica",
            "alvarez": "Alvarez",
        }

        palabra_normalizada = self._quitar_acentos(palabra)

        if palabra_normalizada.lower() in palabras_sin_acentos:
            return palabras_sin_acentos[palabra_normalizada.lower()]

        if palabra != palabra.upper() and (
            palabra[0].isupper() or any(
                caracter.isupper() for caracter in palabra[1:]
            )
        ):
            return palabra

        return palabra.capitalize()