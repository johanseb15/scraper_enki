from copy import deepcopy

import pytest

from src.dominio.semantic_observation import ObservationUnderstandingStatus, SemanticObservationRole
from src.infraestructura.semantic_observation_adapter import (
    SemanticObservationAdapterError,
    semantic_observation_from_normalized_row,
)


def _normalized_row(**kwargs):
    row = {
        "observation_id": "4",
        "source": "jadetech_generic",
        "province": "Córdoba",
        "city": "Córdoba",
        "economic_object_raw": "BackUp de Datos cada 100gb Extras Categorías: Servicio técnico",
        "price_value": "42120",
        "currency": "ARS",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "LOCAL_SERVICE",
        "matched_services": "BACKUP_DATOS",
        "canonical_service": "BACKUP_DATOS",
        "comparability_key": "Córdoba::BACKUP_DATOS",
        "original_comparable_status": "INDETERMINATE",
        "extractor_version": "generic_price_extractor_v3",
    }
    row.update(kwargs)
    return row


def _observation_row(**kwargs):
    row = {
        "observation_id": "4",
        "source": "jadetech_generic",
        "provider": "Jadetech",
        "source_url": "https://jadetech.com.ar/categoria/servicio-tecnico/",
        "province": "Córdoba",
        "city": "Córdoba",
        "economic_object_raw": "BackUp de Datos cada 100gb Extras Categorías: Servicio técnico",
        "price_raw": "$ 42.120,00",
        "price_value": "42120",
        "currency": "ARS",
        "extractor_version": "generic_price_extractor_v3",
    }
    row.update(kwargs)
    return row


def test_single_service_row_becomes_fully_represented_observation():
    observation = semantic_observation_from_normalized_row(
        _normalized_row(),
        observation_row=_observation_row(),
        interpretation_reference="semantic_normalization.csv",
        interpretation_version="v2",
    )

    assert observation.semantic_role is SemanticObservationRole.SINGLE_SERVICE
    assert observation.understanding_status is ObservationUnderstandingStatus.FULLY_REPRESENTED
    assert observation.raw_expression == "BackUp de Datos cada 100gb Extras Categorías: Servicio técnico"
    assert observation.canonical_service == "BACKUP_DATOS"
    assert observation.matched_services == ("BACKUP_DATOS",)


def test_composite_row_preserves_matched_services_without_price_decomposition():
    observation = semantic_observation_from_normalized_row(
        _normalized_row(
            semantic_role="COMPOSITE_SERVICE",
            market_scope="MIXED_OR_UNKNOWN",
            canonical_service="",
            matched_services="FORMATEO_INSTALACION_SO|BACKUP_DATOS",
            economic_object_raw="Formateo + backup",
        ),
        interpretation_reference="semantic_normalization.csv",
    )

    assert observation.understanding_status is ObservationUnderstandingStatus.PARTIALLY_UNDERSTOOD
    assert observation.matched_services == ("FORMATEO_INSTALACION_SO", "BACKUP_DATOS")
    assert observation.canonical_service is None
    assert not hasattr(observation, "allocated_price")


@pytest.mark.parametrize(
    ("role", "market_scope"),
    [
        ("SCOPE_DEVICE", "NONE"),
        ("PRICE_CONTEXT", "NONE"),
        ("LOGISTICS_CONTEXT", "NONE"),
        ("NON_OBJECT", "NONE"),
    ],
)
def test_classified_only_rows_preserve_role_without_service_invention(role, market_scope):
    observation = semantic_observation_from_normalized_row(
        _normalized_row(
            semantic_role=role,
            market_scope=market_scope,
            canonical_service="",
            matched_services="",
            economic_object_raw=f"{role} raw text",
        ),
        interpretation_reference="semantic_normalization.csv",
    )

    assert observation.semantic_role.value == role
    assert observation.understanding_status is ObservationUnderstandingStatus.CLASSIFIED_ONLY
    assert observation.canonical_service is None


def test_hardware_product_preserves_goods_market_without_service_invention():
    observation = semantic_observation_from_normalized_row(
        _normalized_row(
            semantic_role="HARDWARE_PRODUCT",
            market_scope="GOODS_MARKET",
            canonical_service="",
            matched_services="",
            economic_object_raw="RYZEN 5700X CPU RTX 3080 GPU",
        ),
        interpretation_reference="semantic_normalization.csv",
    )

    assert observation.semantic_role is SemanticObservationRole.HARDWARE_PRODUCT
    assert observation.market_scope == "GOODS_MARKET"
    assert observation.canonical_service is None


def test_unmapped_row_remains_unknown():
    observation = semantic_observation_from_normalized_row(
        _normalized_row(
            semantic_role="UNMAPPED",
            market_scope="UNKNOWN",
            canonical_service="",
            matched_services="",
            economic_object_raw="texto no interpretado",
        ),
        interpretation_reference="semantic_normalization.csv",
    )

    assert observation.semantic_role is SemanticObservationRole.UNMAPPED
    assert observation.understanding_status is ObservationUnderstandingStatus.UNKNOWN


def test_raw_expression_is_preserved_exactly():
    raw = "Instalación Completa de Sistema Operativo MÁS POPULAR"

    observation = semantic_observation_from_normalized_row(
        _normalized_row(economic_object_raw=raw),
        interpretation_reference="semantic_normalization.csv",
    )

    assert observation.raw_expression == raw


def test_observation_provenance_uses_real_observation_identity_and_source():
    observation = semantic_observation_from_normalized_row(
        _normalized_row(),
        observation_row=_observation_row(),
        interpretation_reference="semantic_normalization.csv",
    )

    assert observation.observation_provenance.origin_type == "COMMERCIAL_OBSERVATION"
    assert observation.observation_provenance.origin_reference == (
        "source=jadetech_generic;observation_id=4;url=https://jadetech.com.ar/categoria/servicio-tecnico/"
    )
    assert observation.provider == "Jadetech"


def test_interpretation_provenance_preserves_normalization_process_reference():
    observation = semantic_observation_from_normalized_row(
        _normalized_row(),
        interpretation_reference="semantic_normalization.csv",
        interpretation_version="v2",
    )

    assert observation.interpretation_provenance.origin_type == "SEMANTIC_NORMALIZATION"
    assert observation.interpretation_provenance.origin_reference == "semantic_normalization.csv"
    assert observation.interpretation_provenance.origin_version == "v2"


def test_interpretation_provenance_can_be_explicitly_unknown():
    observation = semantic_observation_from_normalized_row(_normalized_row())

    assert observation.interpretation_provenance.origin_type == "UNKNOWN"
    assert observation.interpretation_provenance.origin_reference == "UNKNOWN_INTERPRETATION_PROVENANCE"


def test_future_unknown_role_fails_explicitly_instead_of_silent_coercion():
    with pytest.raises(SemanticObservationAdapterError) as exc:
        semantic_observation_from_normalized_row(
            _normalized_row(semantic_role="FUTURE_ROLE"),
            interpretation_reference="semantic_normalization.csv",
        )

    assert "Unknown semantic_role" in str(exc.value)


def test_conversion_is_deterministic_and_does_not_mutate_input():
    row = _normalized_row()
    original = deepcopy(row)

    first = semantic_observation_from_normalized_row(
        row,
        observation_row=_observation_row(),
        interpretation_reference="semantic_normalization.csv",
    )
    second = semantic_observation_from_normalized_row(
        row,
        observation_row=_observation_row(),
        interpretation_reference="semantic_normalization.csv",
    )

    assert first == second
    assert row == original
