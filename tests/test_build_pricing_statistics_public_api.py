import csv
from pathlib import Path

from scripts.build_pricing_statistics import build_pricing_statistics


FIELDS = [
    "observation_id", "source", "province", "city", "economic_object_raw",
    "price_value", "currency", "semantic_role", "market_scope",
    "matched_services", "canonical_service", "comparability_key",
    "original_comparable_status", "extractor_version",
]


def _write_semantic(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def test_build_pricing_statistics_public_api(tmp_path):
    normalization = tmp_path / "semantic.csv"
    local_out = tmp_path / "local.csv"
    remote_out = tmp_path / "remote.csv"

    base = {
        "observation_id": "1",
        "source": "provider_a",
        "province": "Córdoba",
        "city": "Córdoba",
        "economic_object_raw": "Formateo",
        "price_value": "50000",
        "currency": "ARS",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "LOCAL_SERVICE",
        "matched_services": "FORMATEO_INSTALACION_SO",
        "canonical_service": "FORMATEO_INSTALACION_SO",
        "comparability_key": "Córdoba::FORMATEO_INSTALACION_SO",
        "original_comparable_status": "INDETERMINATE",
        "extractor_version": "generic_price_extractor_v3",
    }
    remote = dict(base)
    remote.update({
        "observation_id": "2",
        "source": "provider_b",
        "province": "CABA",
        "economic_object_raw": "Soporte remoto",
        "price_value": "35000",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "matched_services": "SOPORTE_REMOTO",
        "canonical_service": "SOPORTE_REMOTO",
        "comparability_key": "AR::SOPORTE_REMOTO",
    })

    _write_semantic(normalization, [base, remote])

    local, remote_rows = build_pricing_statistics(
        normalization,
        local_out_path=local_out,
        remote_out_path=remote_out,
    )

    assert len(local) == 1
    assert local[0]["market"] == "Córdoba"
    assert local[0]["canonical_service"] == "FORMATEO_INSTALACION_SO"
    assert len(remote_rows) == 1
    assert remote_rows[0]["market"] == "AR"
    assert remote_rows[0]["canonical_service"] == "SOPORTE_REMOTO"
    assert local_out.exists()
    assert remote_out.exists()

    # TD-010: semantic normalization alone carries source identity,
    # not stable provider identity. Legacy loading must fail closed
    # instead of treating source_id as provider independence.
    assert local[0]["source_count"] == 1
    assert local[0]["providers_n"] == 0
    assert local[0]["evidence_confidence"] == "INSUFFICIENT"
    assert local[0]["decision_ready"] == "NO"
    assert local[0]["range_ready"] == "NO"

    assert remote_rows[0]["source_count"] == 1
    assert remote_rows[0]["providers_n"] == 0
    assert remote_rows[0]["evidence_confidence"] == "INSUFFICIENT"
    assert remote_rows[0]["decision_ready"] == "NO"
    assert remote_rows[0]["range_ready"] == "NO"

    with local_out.open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        local_csv = list(csv.DictReader(handle))

    assert local_csv[0]["source_count"] == "1"
    assert local_csv[0]["providers_n"] == "0"

def test_legacy_builder_counts_stable_provider_not_sources():
    from src.dominio.economic_evidence import (
        DimensionClaim,
        DimensionOrigin,
        DimensionStatus,
        DimensionValue,
        EconomicEvidenceDimensionsV2,
        ProviderIdentity,
    )
    from src.dominio.semantic_knowledge import KnowledgeProvenance
    from scripts.build_pricing_statistics import _build

    def provider_dimensions(
        provider_id: str,
        *,
        source: str,
    ):
        provider = ProviderIdentity(
            provider_id=provider_id,
            provider_name="Shared Provider",
            source=source,
        )

        return EconomicEvidenceDimensionsV2(
            provider_identity=DimensionValue(
                value=provider,
                status=DimensionStatus.INFERRED,
                claims=(
                    DimensionClaim(
                        value=provider,
                        origin=DimensionOrigin.REGISTRY_CLAIM,
                        provenance=KnowledgeProvenance(
                            "PROVIDER_SOURCE_REGISTRY",
                            (
                                f"source={source};"
                                "provider=Shared Provider"
                            ),
                            "pricing-source-registry-v1",
                        ),
                        raw_basis=(
                            f"registry source={source!r} "
                            "provider='Shared Provider'"
                        ),
                    ),
                ),
            ),
        )

    base = {
        "province": "Córdoba",
        "city": "Córdoba",
        "economic_object_raw": "Formateo",
        "currency": "ARS",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "LOCAL_SERVICE",
        "canonical_service": "FORMATEO_INSTALACION_SO",
    }

    first = dict(
        base,
        observation_id="1",
        source="source-a",
        price_value="50000",
    )

    second = dict(
        base,
        observation_id="2",
        source="source-b",
        price_value="55000",
    )

    dimensions = {
        "1": provider_dimensions(
            "provider:shared:abc",
            source="source-a",
        ),
        "2": provider_dimensions(
            "provider:shared:abc",
            source="source-b",
        ),
    }

    result = _build(
        [first, second],
        market_scope="LOCAL_SERVICE",
        provider_dimensions=dimensions,
    )

    assert len(result) == 1

    cohort = result[0]

    assert cohort["observations_n"] == 2
    assert cohort["source_count"] == 2
    assert cohort["providers_n"] == 1
    assert cohort["evidence_confidence"] == "INSUFFICIENT"
    assert cohort["range_ready"] == "NO"

def test_public_api_counts_same_provider_across_two_sources_once(tmp_path):
    from src.infraestructura.economic_dimensions_v2_artifact import (
        build_economic_dimensions_v2_sidecar,
    )

    normalization = tmp_path / "semantic-shared-provider.csv"
    local_out = tmp_path / "local-shared-provider.csv"
    remote_out = tmp_path / "remote-shared-provider.csv"
    registry = tmp_path / "registry.csv"
    dimensions = tmp_path / "dimensions-v2.jsonl"

    first = {
        "observation_id": "101",
        "source": "source_a",
        "province": "Córdoba",
        "city": "Córdoba",
        "economic_object_raw": "Formateo",
        "price_value": "50000",
        "currency": "ARS",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "LOCAL_SERVICE",
        "matched_services": "FORMATEO_INSTALACION_SO",
        "canonical_service": "FORMATEO_INSTALACION_SO",
        "comparability_key": "Córdoba::FORMATEO_INSTALACION_SO",
        "original_comparable_status": "INDETERMINATE",
        "extractor_version": "generic_price_extractor_v3",
    }

    second = dict(first)
    second.update({
        "observation_id": "102",
        "source": "source_b",
        "price_value": "55000",
    })

    _write_semantic(
        normalization,
        [first, second],
    )

    registry.write_text(
        "source,provider,url\n"
        "source_a,Shared Provider,https://example.test/a\n"
        "source_b,Shared Provider,https://example.test/b\n",
        encoding="utf-8",
    )

    build_economic_dimensions_v2_sidecar(
        normalization,
        registry,
        dimensions,
        version="td010-test-v1",
    )

    local, remote = build_pricing_statistics(
        normalization,
        local_out_path=local_out,
        remote_out_path=remote_out,
        dimensions_path=dimensions,
    )

    assert remote == []
    assert len(local) == 1

    cohort = local[0]

    assert cohort["observations_n"] == 2
    assert cohort["source_count"] == 2
    assert cohort["providers_n"] == 1
    assert cohort["evidence_confidence"] == "INSUFFICIENT"
    assert cohort["range_ready"] == "NO"
    assert cohort["decision_ready"] == "NO"

    with local_out.open(
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        persisted = next(csv.DictReader(handle))

    assert persisted["source_count"] == "2"
    assert persisted["providers_n"] == "1"
