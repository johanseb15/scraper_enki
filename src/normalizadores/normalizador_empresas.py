import re
import unicodedata


class NormalizadorEmpresas:
    """
    Normaliza nombres de empresas para comparabilidad.

    Responsabilidades:
    - eliminar sufijos legales
    - limpiar ruido tipográfico
    - corregir casing
    - preservar nombres comerciales CamelCase
    - preservar acentos originales
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
        "IT": "IT",
    }

    EXCEPCIONES_CANONICAS = {
        "informatica": "Informatica",
        "alvarez": "Alvarez",
    }

    def normalizar(self, nombre_crudo: str) -> str:

        if not nombre_crudo:
            return ""

        nombre = nombre_crudo.strip()

        tenia_sufijo_legal = False

        for sufijo in self.SUFIJOS_LEGALES:

            if re.search(
                sufijo,
                nombre,
                flags=re.IGNORECASE
            ):
                tenia_sufijo_legal = True

            nombre = re.sub(
                sufijo,
                "",
                nombre,
                flags=re.IGNORECASE
            )


        nombre = re.sub(
            r"[^\w\sáéíóúÁÉÍÓÚñÑ]",
            "",
            nombre
        )


        nombre = re.sub(
            r"\s+",
            " ",
            nombre
        ).strip()


        palabras = nombre.split()

        resultado = []


        for indice, palabra in enumerate(palabras):

            # Solo para comparación
            palabra_sin_acentos = self._quitar_acentos(
                palabra
            )

            clave = palabra_sin_acentos.lower()


            # Excepciones canonizadas
            if clave in self.EXCEPCIONES_CANONICAS:

                resultado.append(
                    self.EXCEPCIONES_CANONICAS[clave]
                )

                continue


            # Mantener siglas
            if (
                palabra_sin_acentos.upper()
                in self.SIGLAS_MANTENER
                and not (
                    tenia_sufijo_legal
                    and indice == len(palabras)-1
                )
            ):

                resultado.append(
                    self.SIGLAS_MANTENER[
                        palabra_sin_acentos.upper()
                    ]
                )

                continue


            # IMPORTANTE:
            # usamos palabra original
            # para conservar acentos
            resultado.append(
                self._normalizar_casing(
                    palabra
                )
            )


        return " ".join(resultado)



    def _normalizar_casing(self, palabra: str) -> str:
        """
        Corrige casing sin destruir CamelCase.
        """

        if (
            any(c.isupper() for c in palabra[1:])
            and not palabra.isupper()
        ):
            return palabra


        if palabra.isupper():
            return palabra.capitalize()


        if palabra.islower():
            return palabra.capitalize()


        return palabra



    def _quitar_acentos(self, texto: str) -> str:
        """
        Uso interno solamente.

        Córdoba -> Cordoba
        Informática -> Informatica
        """

        normalizado = unicodedata.normalize(
            "NFD",
            texto
        )

        return "".join(
            caracter
            for caracter in normalizado
            if unicodedata.category(caracter) != "Mn"
        )