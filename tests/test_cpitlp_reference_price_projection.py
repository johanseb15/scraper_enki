import hashlib
import importlib

TARGET = "TÉCNICO HARDWARE/SOFTWARE ($/hora)"
TEXT = (
    "Honorarios de Referencia – Ciencias Informáticas "
    "con vigencia a partir del día 01 de septiembre de 2.026. "
    f"{TARGET}$ 33.193 Responsable de Servicio Técnico $ 47.120"
)


def raw_document(text=TEXT):
    return bytes.fromhex("d0cf11e0a1b11ae1") + text.encode("utf-16le")


def project(raw, price_raw="$ 33.193", **overrides):
    module = importlib.import_module(
        "src.infraestructura.cpitlp_reference_price_projection"
    )
    arguments = dict(
        source_id="cpitlp_it_resolution_2026_09",
        source_url="https://example.org/reference.doc",
        content_hash=hashlib.sha256(raw).hexdigest(),
        economic_object_raw=TARGET,
        price_raw=price_raw,
    )
    arguments.update(overrides)
    return module.build_cpitlp_reference_price_observation(raw, **arguments)


def test_projects_exact_reference_price_from_primary_word():
    raw = raw_document()
    observation = project(raw)
    assert observation is not None
    assert observation.economic_object_raw == TARGET
    assert observation.price_raw == "$ 33.193"
    assert observation.price_value == 33193
    assert observation.currency_raw == "ARS"
    assert observation.unit_raw == "PER_HOUR"
    assert observation.price_semantics == "PROFESSIONAL_REFERENCE"
    assert observation.raw_document_identity == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert observation.source == "CPITLP"
    assert observation.source_id == "cpitlp_it_resolution_2026_09"
    assert observation.source_url == "https://example.org/reference.doc"


def test_target_cannot_take_price_after_another_row_label():
    raw = raw_document(TEXT.replace("$ 33.193 ", ""))
    assert project(raw, price_raw="$ 47.120") is None


def test_rejects_non_ole():
    assert project(TEXT.encode("utf-16le")) is None


def test_rejects_missing_informatics_scope():
    assert project(raw_document(TEXT.replace("Ciencias Informáticas", "Arquitectura"))) is None


def test_rejects_missing_target():
    assert project(raw_document(TEXT.replace(TARGET, "HARDWARE/SOFTWARE"))) is None


def test_rejects_other_price_in_same_document():
    assert project(raw_document(), price_raw="$ 47.120") is None


def test_rejects_mismatched_raw_hash():
    assert project(raw_document(), content_hash="0" * 64) is None


def test_accepts_word_cell_separator_without_requiring_temporal_facts():
    text = f"Honorarios de Referencia – Ciencias Informáticas {TARGET}\x07$ 33.193"
    observation = project(raw_document(text))
    assert observation is not None
    assert observation.price_value == 33193


def test_rejects_unsupported_numeric_format():
    assert project(raw_document(TEXT.replace("33.193", "33,193")), price_raw="$ 33,193") is None


def test_same_raw_composition_with_separate_temporal_authority():
    from dataclasses import fields
    from src.infraestructura.cpitlp_temporal_reference_extractor import (
        build_cpitlp_temporal_reference_claim,
    )

    raw = raw_document()
    observation = project(raw)
    claim = build_cpitlp_temporal_reference_claim(
        raw,
        source_id="cpitlp_it_resolution_2026_09",
        source_url="https://example.org/reference.doc",
        acquired_at=None,
        content_hash=hashlib.sha256(raw).hexdigest(),
        economic_object_raw=TARGET,
        price_raw="$ 33.193",
    )
    assert observation is not None
    assert claim is not None
    assert observation.raw_document_identity == claim.raw_document_id
    assert observation.economic_object_raw == claim.economic_object_raw
    assert observation.price_raw == claim.price_raw
    assert claim.valid_from == "2026-09-01"
    assert not {"valid_from", "valid_to"} & {field.name for field in fields(observation)}
