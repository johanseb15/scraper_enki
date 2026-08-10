from typing import Protocol

from src.dominio.evidencia import ConsultaUsuarioRaw, FuenteCandidata


class RepositorioEvidencia(Protocol):
    def guardar_lenguaje(self, registro: ConsultaUsuarioRaw) -> bool:
        """Guarda un registro; devuelve False cuando ya existía."""

    def guardar_fuente(self, fuente: FuenteCandidata) -> bool:
        """Guarda una fuente; devuelve False cuando ya existía."""
