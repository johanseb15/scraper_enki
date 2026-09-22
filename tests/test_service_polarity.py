import pytest

from src.dominio.service_polarity import explicit_backup_excluded


@pytest.mark.parametrize(
    "text",
    (
        "formateo sin backup",
        "formateo sin respaldo",
        "formateo no incluye backup",
        "formateo no incluye copia de seguridad",
    ),
)
def test_explicit_backup_exclusion_variants_are_detected(text):
    assert explicit_backup_excluded(text) is True


@pytest.mark.parametrize(
    "text",
    (
        "formateo con backup",
        "formateo con respaldo",
        "incluye backup",
        "incluyendo copia de seguridad",
    ),
)
def test_positive_backup_mentions_are_not_exclusions(text):
    assert explicit_backup_excluded(text) is False
