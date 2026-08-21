from src.aplicacion.parser_consulta_pricing import parse_pricing_query


def test_technical_symptoms_do_not_become_hardware_repair_aliases():
    for query in (
        "no prende",
        "pantalla negra",
        "error de memoria",
    ):
        parsed = parse_pricing_query(query)

        assert "REPARACION_HARDWARE" not in parsed.canonical_services
        assert parsed.canonical_services == ()
        assert parsed.technical_need is None
        assert parsed.metadata.clarification_reason == "UNKNOWN_ECONOMIC_OBJECT"


def test_cleaning_notebook_is_not_reused_for_slow_notebook_symptom():
    cleaning = parse_pricing_query("limpiar notebook")
    symptom = parse_pricing_query("notebook esta lenta")

    assert cleaning.canonical_services == ()
    assert symptom.canonical_services == ()
    assert cleaning.metadata.clarification_reason == "UNKNOWN_ECONOMIC_OBJECT"
    assert symptom.metadata.clarification_reason == "UNKNOWN_ECONOMIC_OBJECT"


def test_existing_golden_cleaning_phrase_remains_unknown_without_new_alias():
    parsed = parse_pricing_query(
        "quiero cobrar 60 lucas por limpiar notebook y cambiar pasta, está bien o me bajo?"
    )

    assert "LIMPIEZA_MANTENIMIENTO" not in parsed.canonical_services
    assert parsed.canonical_services == ()
    assert parsed.metadata.clarification_reason == "UNKNOWN_ECONOMIC_OBJECT"
