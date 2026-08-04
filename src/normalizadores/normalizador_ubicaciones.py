from src.dominio.ubicacion import Ubicacion


class NormalizadorUbicaciones:
    """
    Normaliza variantes geográficas para permitir comparaciones
    consistentes entre ofertas.
    """

    PROVINCIAS = {
        "cordoba": "Córdoba",
        "córdoba": "Córdoba",
        "cordoba capital": "Córdoba",
    }

    CIUDADES = {
        "cba": "Córdoba",
        "cba.": "Córdoba",
        "cordoba": "Córdoba",
        "córdoba": "Córdoba",
        "ciudad de cordoba": "Córdoba",
        "ciudad de córdoba": "Córdoba",
    }

    def normalizar(
        self,
        provincia: str,
        ciudad: str
    ) -> Ubicacion:

        provincia_normalizada = self._normalizar_provincia(provincia)
        ciudad_normalizada = self._normalizar_ciudad(ciudad)

        return Ubicacion(
            provincia=provincia_normalizada,
            ciudad=ciudad_normalizada,
        )

    def _normalizar_provincia(self, provincia: str) -> str:
        clave = provincia.lower().strip()

        return self.PROVINCIAS.get(
            clave,
            provincia.strip()
        )

    def _normalizar_ciudad(self, ciudad: str) -> str:
        clave = ciudad.lower().strip()

        return self.CIUDADES.get(
            clave,
            ciudad.strip()
        )