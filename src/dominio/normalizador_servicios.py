import unicodedata
from src.dominio.servicios import ServicioCanonico


class NormalizadorServicios:
    def __init__(self) -> None:
        self._alias_map: dict[str, ServicioCanonico] = {
            # Malware
            "eliminacion de malware": ServicioCanonico.MALWARE,
            "eliminacion de malware / spyware": ServicioCanonico.MALWARE,
            # Formateo
            "formateo e instalacion de so": ServicioCanonico.FORMATEO,
            "instalacion de windows 11": ServicioCanonico.FORMATEO,
            # Mantenimiento
            "mantenimiento preventivo": ServicioCanonico.MANTENIMIENTO,
            "limpieza fisica de pc": ServicioCanonico.MANTENIMIENTO,
            # Redes
            "diagnostico y soporte de redes": ServicioCanonico.SOPORTE_REDES,
            "configuracion de router": ServicioCanonico.SOPORTE_REDES,
        }

    def _normalizar_clave(self, texto: str) -> str:
        """Limpia espacios, pasa a minúsculas y remueve acentos."""
        texto_limpio = texto.strip().lower()

        # Remueve tildes/acentos
        texto_nfkd = unicodedata.normalize("NFKD", texto_limpio)
        return "".join(c for c in texto_nfkd if not unicodedata.combining(c))

    def normalizar(self, texto: str) -> ServicioCanonico | str:
        """Devuelve el Enum normalizado o el texto original si no existe alias."""
        clave = self._normalizar_clave(texto)
        return self._alias_map.get(clave, texto)