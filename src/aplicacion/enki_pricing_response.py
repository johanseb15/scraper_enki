from __future__ import annotations

from dataclasses import dataclass

from src.aplicacion.enki_pricing_query_service import EnkiPricingQueryResult


@dataclass(frozen=True)
class EnkiUserResponse:
    headline: str
    summary: str
    evidence_line: str | None = None
    caveat: str | None = None


def _money(value) -> str:
    if value is None:
        return "-"
    n = int(round(float(value)))
    return f"${n:,.0f}".replace(",", ".")


def presentar_resultado_pricing(result: EnkiPricingQueryResult) -> EnkiUserResponse:
    """Translate structured Enki evidence into a concise user-facing answer.

    This layer never changes evidence, thresholds, confidence or decision labels.
    It only renders already-authorized conclusions.
    """
    if result.status == "CLARIFICATION_REQUIRED":
        question = (
            result.clarification_question
            or "Necesito un dato más para comparar correctamente."
        )
        return EnkiUserResponse(
            headline="Necesito una aclaración",
            summary=question,
            caveat=result.clarification_reason,
        )

    if result.status == "UNSUPPORTED_QUERY":
        return EnkiUserResponse(
            headline="Todavía no puedo comparar esta consulta",
            summary="La consulta está fuera del alcance seguro de Enki Decision v1.",
            caveat=result.unsupported_reason,
        )

    e = result.evidence
    if e is None:
        return EnkiUserResponse(
            headline="Sin evidencia disponible",
            summary="No encontré una cohorte comparable para esta consulta.",
        )

    evidence_line = (
        f"Rango observado {_money(e.min_ars)}–{_money(e.max_ars)}; "
        f"mediana {_money(e.median_ars)}; "
        f"{e.observations_n} precios de {e.providers_n} proveedores."
    )

    if result.status == "DECISION_READY":
        label = e.decision_label or "SIN_DECISION"
        if label == "BAJO":
            summary = (
                f"El precio consultado está bajo para esta cohorte. "
                f"El 25% central inferior comienza en {_money(e.q1_ars)}."
            )
        elif label == "ALTO":
            summary = (
                f"El precio consultado está alto para esta cohorte. "
                f"El cuartil superior comienza por encima de {_money(e.q3_ars)}."
            )
        else:
            summary = (
                f"El precio consultado está dentro del rango razonable de la cohorte "
                f"({_money(e.q1_ars)}–{_money(e.q3_ars)})."
            )
        return EnkiUserResponse(
            headline=label,
            summary=summary,
            evidence_line=evidence_line,
            caveat=f"Confianza de evidencia: {e.evidence_confidence}.",
        )

    if result.status == "RANGE_READY":
        return EnkiUserResponse(
            headline="Rango de mercado disponible",
            summary=(
                "Hay evidencia suficiente para mostrar un rango empírico, "
                "pero no para emitir BAJO/RAZONABLE/ALTO."
            ),
            evidence_line=evidence_line,
            caveat=f"Confianza de evidencia: {e.evidence_confidence}.",
        )

    if result.status == "INSUFFICIENT_EVIDENCE":
        return EnkiUserResponse(
            headline="Evidencia insuficiente",
            summary=(
                "Hay precios observados, pero la muestra o diversidad de proveedores "
                "todavía no alcanza para una decisión confiable."
            ),
            evidence_line=evidence_line,
            caveat="Enki retiene la decisión en lugar de sobreinterpretar la muestra.",
        )

    if result.status == "NO_EVIDENCE":
        return EnkiUserResponse(
            headline="Sin evidencia comparable",
            summary="No encontré precios comparables para este servicio y mercado.",
        )

    return EnkiUserResponse(
        headline=result.status,
        summary="Resultado disponible sin una presentación específica.",
        evidence_line=evidence_line,
    )
