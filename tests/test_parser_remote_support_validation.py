import pytest

from src.aplicacion.parser_consulta_pricing import parse_pricing_query


@pytest.mark.parametrize("service", ["soporte remoto", "soporte técnico remoto"])
def test_recognizes_remote_support_without_requiring_decision_ready(service):
    parsed = parse_pricing_query(
        f"Cobro 35000 pesos por una hora de {service} en Argentina, ¿es razonable?"
    )

    assert parsed.canonical_services == ("SOPORTE_REMOTO",)
    assert "UNKNOWN_ECONOMIC_OBJECT" not in (parsed.metadata.clarification_reason or "")
