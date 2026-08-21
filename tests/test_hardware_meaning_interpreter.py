import pytest

from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import (
    HardwareMeaningKind,
    HardwareUnderstandingStatus,
    SemanticObservation,
    SemanticObservationRole,
)
from src.infraestructura.hardware_meaning_interpreter import interpret_hardware_meaning


def _prov(kind="SEMANTIC_NORMALIZATION", reference="semantic.csv"):
    return KnowledgeProvenance(kind, reference, "v1")


def _hardware(raw):
    return SemanticObservation(
        observation_id="1",
        raw_expression=raw,
        semantic_role=SemanticObservationRole.HARDWARE_PRODUCT,
        market_scope="GOODS_MARKET",
        source="mobo_mdp_ba",
        provider="MOBO",
        province="Buenos Aires",
        observation_provenance=_prov("COMMERCIAL_OBSERVATION", "row:1"),
        interpretation_provenance=_prov(),
    )


def test_single_gpu_product_is_understood_without_becoming_service():
    obs = _hardware("Placas de video MOBO RTX 3090 24 GB Agregar al carrito")
    meaning = interpret_hardware_meaning(obs)
    assert obs.canonical_service is None
    assert meaning.meaning_kind is HardwareMeaningKind.SINGLE_COMPONENT_FAMILY
    assert meaning.families == ("GPU",)
    assert meaning.understanding_status is HardwareUnderstandingStatus.UNDERSTOOD
    assert not hasattr(meaning, "canonical_service")


def test_multi_component_system_preserves_multiple_families_without_price_decomposition():
    meaning = interpret_hardware_meaning(
        _hardware("RYZEN 5 7600 CPU 6700XT GPU DDR5 16GB RAM M2 1TB Storage")
    )
    assert meaning.meaning_kind is HardwareMeaningKind.MULTI_COMPONENT_SYSTEM
    assert set(meaning.families) >= {"CPU", "GPU", "MEMORY", "STORAGE"}
    assert meaning.understanding_status is HardwareUnderstandingStatus.UNDERSTOOD
    assert not hasattr(meaning, "allocated_prices")


def test_service_like_hardware_role_is_exposed_as_conflict_not_product_truth():
    meaning = interpret_hardware_meaning(
        _hardware("Cambio de componente (RAM, GPU, disco, etc.)PC")
    )
    assert meaning.meaning_kind is HardwareMeaningKind.SERVICE_LIKE_CONFLICT
    assert meaning.understanding_status is HardwareUnderstandingStatus.AMBIGUOUS
    assert set(meaning.families) >= {"GPU", "MEMORY", "STORAGE"}


def test_brand_variant_and_specs_are_optional_evidence_signals():
    meaning = interpret_hardware_meaning(
        _hardware("Placas de video MOBO RX 580 8GB MSI ARMOR OC Agregar al carrito")
    )
    assert meaning.families == ("GPU",)
    assert "MSI" in meaning.brand_signals
    assert "OC" in meaning.variant_signals
    assert "8GB" in meaning.spec_signals


def test_unknown_hardware_stays_unknown():
    meaning = interpret_hardware_meaning(_hardware("producto tecnológico sin detalle"))
    assert meaning.meaning_kind is HardwareMeaningKind.UNKNOWN
    assert meaning.understanding_status is HardwareUnderstandingStatus.UNKNOWN


def test_raw_and_provenance_are_preserved():
    raw = "Placas de video MOBO GTX 1660 SUPER 6GB EVGA SC ULTRA Agregar al carrito"
    obs = _hardware(raw)
    meaning = interpret_hardware_meaning(obs)
    assert meaning.source_expression == raw
    assert meaning.provenance == obs.interpretation_provenance


def test_interpreter_rejects_non_hardware_observation():
    obs = _hardware("RTX 3090")
    object.__setattr__(obs, "semantic_role", SemanticObservationRole.SCOPE_DEVICE)
    with pytest.raises(ValueError, match="HARDWARE_PRODUCT"):
        interpret_hardware_meaning(obs)


def test_hardware_meaning_does_not_change_existing_parser_runtime():
    from src.aplicacion.parser_consulta_pricing import parse_pricing_query
    before = parse_pricing_query("cuánto sale instalar Windows")
    interpret_hardware_meaning(_hardware("Placas de video MOBO RTX 3090 24 GB"))
    after = parse_pricing_query("cuánto sale instalar Windows")
    assert after == before
