from src.aplicacion.parser_consulta_pricing import (
    parse_pricing_query,
)
from src.aplicacion.user_query_understanding_projector import (
    project_user_query_understanding,
)


HUMAN_REAL_COMPOSITION_QUERY = (
    "Cuanto cobran, mano de obra + pendrive de 64gb "
    "(sale 25.000) = backup? Yo cobre 65.000, "
    "pendrive + mano de obra y ya le queda un pendrive "
    "con toda su info"
)


def test_multiple_real_unknowns_produce_ordered_typed_clarifications():
    parsed = parse_pricing_query(
        HUMAN_REAL_COMPOSITION_QUERY,
        language_evidence_type="OBSERVED_USER",
    )

    envelope = project_user_query_understanding(
        parsed,
    )

    assert [
        (
            item.reason,
            item.target_field,
            item.question,
        )
        for item in envelope.clarifications
    ] == [
        (
            "MISSING_PROVINCE",
            "geography.province",
            "\u00bfEn qu\u00e9 provincia se realiza el servicio?",
        ),
        (
            "UNKNOWN_CURRENCY",
            "price.currency",
            "\u00bfEse monto est\u00e1 expresado en pesos argentinos "
            "o en otra moneda?",
        ),
    ]

    assert (
        parsed.metadata.clarification_question
        == envelope.clarifications[0].question
    )

    assert envelope.clarification_reasons == (
        "MISSING_PROVINCE",
        "UNKNOWN_CURRENCY",
    )
