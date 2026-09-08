from dataclasses import fields

from src.dominio import evidencia


def test_reference_price_is_a_separate_first_class_observation():
    observation = evidencia.RegistroPrecioReferenciaObservado(
        raw_document_identity="sha256:" + "a" * 64,
        source="CPITLP",
        source_id="cpitlp_it_resolution_2026_09",
        source_url="https://example.org/reference.doc",
        extractor_version="cpitlp-reference-price-v1",
        economic_object_raw="TÉCNICO HARDWARE/SOFTWARE ($/hora)",
        price_raw="$ 33.193",
        price_value=33193,
        currency_raw="ARS",
        unit_raw="PER_HOUR",
    )
    assert not isinstance(observation, evidencia.RegistroPrecioComercialObservado)
    assert observation.price_semantics == "PROFESSIONAL_REFERENCE"
    assert observation.raw_document_identity == "sha256:" + "a" * 64
    assert not {"valid_from", "valid_to", "provider_raw", "storage_id"} & {
        field.name for field in fields(observation)
    }
