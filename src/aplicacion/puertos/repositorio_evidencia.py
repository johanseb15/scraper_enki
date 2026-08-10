from typing import Protocol

from src.dominio.evidencia import (
    ConsultaUsuarioRaw,
    DocumentoRaw,
    FuenteCandidata,
    RegistroContratacionObservado,
)


class RepositorioEvidencia(Protocol):
    def guardar_lenguaje(self, registro: ConsultaUsuarioRaw) -> bool:
        """Guarda un registro; devuelve False cuando ya existia."""

    def guardar_fuente(self, fuente: FuenteCandidata) -> bool:
        """Guarda una fuente; devuelve False cuando ya existia."""

    def guardar_documento_raw(self, documento: DocumentoRaw) -> bool:
        """Guarda un documento raw; devuelve False cuando ya existia."""

    def guardar_observacion_contratacion(
        self, observacion: RegistroContratacionObservado
    ) -> bool:
        """Guarda una observacion; devuelve False cuando ya existia."""
