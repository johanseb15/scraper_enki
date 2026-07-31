from dataclasses import dataclass, field


@dataclass
class MetricasEjecucion:
    exitosos: list[str] = field(default_factory=list)
    fallidos: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.exitosos) + len(self.fallidos)

    def registrar_exito(self, nombre: str) -> None:
        self.exitosos.append(nombre)

    def registrar_fallo(self, nombre: str) -> None:
        self.fallidos.append(nombre)

    def resumen_texto(self) -> str:
        s_exitosos = ", ".join(self.exitosos) if self.exitosos else "Ninguno"
        s_fallidos = ", ".join(self.fallidos) if self.fallidos else "Ninguno"
        return (
            f"\n=== MÉTRICAS DE EJECUCIÓN ===\n"
            f"Total procesados: {self.total}\n"
            f"  - Exitosos ({len(self.exitosos)}): {s_exitosos}\n"
            f"  - Fallidos  ({len(self.fallidos)}): {s_fallidos}\n"
            f"=============================="
        )


class ResultadoEjecucion(str):
    """Subclase de str que contiene el reporte de texto pero adjunta las métricas de ejecución.
    
    Permite retrocompatibilidad total con tests que esperan isinstance(res, str) o 'texto' in res.
    """

    metricas: MetricasEjecucion

    def __new__(cls, reporte: str, metricas: MetricasEjecucion):
        obj = super().__new__(cls, reporte)
        obj.metricas = metricas
        return obj

    @property
    def reporte(self) -> str:
        return str(self)
