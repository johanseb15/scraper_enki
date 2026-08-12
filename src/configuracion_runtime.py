import os
from os import PathLike


ENKI_DB_PATH = "ENKI_DB_PATH"
RUTA_DB_OFERTAS_DEFAULT = "enki_ofertas.db"


def resolver_ruta_db_ofertas(
    ruta_explicita: str | PathLike[str] | None = None,
) -> str:
    """Resuelve la DB runtime: argumento, entorno y default, en ese orden."""
    if ruta_explicita is not None:
        return os.fspath(ruta_explicita)

    ruta_entorno = os.getenv(ENKI_DB_PATH)
    if ruta_entorno:
        return ruta_entorno

    return RUTA_DB_OFERTAS_DEFAULT
