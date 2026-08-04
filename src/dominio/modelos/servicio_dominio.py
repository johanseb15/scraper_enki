from dataclasses import dataclass, field
from src.dominio.servicios import ServicioCanonico


@dataclass(frozen=True)
class ServicioDominio:
    id: ServicioCanonico
    nombre_display: str
    categoria: str
    sinonimos: tuple[str, ...] = field(default_factory=tuple)

    def coincide_con(self, texto_raw: str) -> bool:
        """Evalúa si una cadena cruda coincide con el nombre o sinónimos."""
        if not texto_raw or not texto_raw.strip():
            return False
        texto_limpio = texto_raw.lower().strip()
        if texto_limpio == self.nombre_display.lower():
            return True
        return any(sinonimo.lower() in texto_limpio for sinonimo in self.sinonimos)