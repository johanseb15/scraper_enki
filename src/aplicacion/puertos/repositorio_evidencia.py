from typing import Protocol

from src.dominio.evidencia import (
    ConsultaUsuarioRaw,
    DocumentoRaw,
    FuenteCandidata,
    RegistroAwardUSASpendingObservado,
    RegistroContratacionObservado,
    RegistroLineaOrdenCompraMercadoPublicoObservada,
    RegistroOrdenCompraMercadoPublicoObservada,
    RegistroFilaArgentinaObservada,
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

    def guardar_observacion_usaspending_award(
        self, observacion: RegistroAwardUSASpendingObservado
    ) -> bool:
        """Guarda una observacion USASpending; devuelve False cuando ya existia."""


    def guardar_observacion_mercado_publico_orden_con_lineas(
        self,
        orden: RegistroOrdenCompraMercadoPublicoObservada,
        lineas: list[RegistroLineaOrdenCompraMercadoPublicoObservada],
    ) -> bool:
        """Guarda una orden observada y sus lineas; devuelve False si ya existia."""


    def guardar_fila_argentina(self, fila: RegistroFilaArgentinaObservada) -> bool:
        """Guarda una fila observada de un CSV oficial argentino; devuelve False si ya existia."""


    def guardar_filas_argentina(self, filas: list[RegistroFilaArgentinaObservada]) -> int:
        """Guarda filas observadas en lote y devuelve cantidad insertada."""
