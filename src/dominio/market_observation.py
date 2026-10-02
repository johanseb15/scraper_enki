from dataclasses import dataclass

from src.dominio.oferta import Oferta


@dataclass(frozen=True)
class MarketObservation:
    """Oferta interpretada junto a la evidencia original y sus límites."""

    id: str
    oferta: Oferta | None
    provider: str
    service: str
    currency: str | None
    modality: str | None
    unit: str | None
    scope: str | None
    province: str | None
    city: str | None
    source_url: str
    captured_at: str | None
    effective_date: str | None
    capture_id: str | None
    raw: dict
    evidence_kind: str
    comparability_established: bool
    comparability_note: str | None = None

    def exclusion_reason(self) -> str | None:
        if self.evidence_kind != "public_capture":
            return "Datos ilustrativos"
        if self.oferta is None or self.oferta.precio <= 0:
            return "Precio inválido o servicio no normalizable"
        if not self.modality:
            return "Modalidad desconocida"
        if not self.capture_id or not self.captured_at or not self.source_url:
            return "Procedencia incompleta"
        if not self.comparability_established or not self.scope or not self.unit or not self.currency:
            return "Comparabilidad no establecida"
        return None
