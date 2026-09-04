from datetime import datetime, timezone
import csv
import hashlib
import importlib

from src.dominio.evidencia import DocumentoRaw
from src.dominio.offer_evidence import (
    EvidenceLineage,
    OfferReachChargedScopeEvidence,
    SourceClaimMethod,
    SourceEconomicClaim,
)
from src.infraestructura.economic_dimensions_v2_adapter import (
    derive_economic_dimensions_v2,
)


class FakeRawRepository:
    def __init__(self, documents):
        self._documents = list(documents)

    def listar_documentos_raw(self, source=None, limit=None):
        documents = self._documents
        if source is not None:
            documents = [
                document
                for document in documents
                if document.source == source
            ]
        if limit is not None:
            documents = documents[:limit]
        return list(documents)


def _csv_rows(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def test_storage_neutral_runtime_builder_fails_closed_without_temporal_evidence(
    tmp_path,
):
    """
    Live runtime construction must consume in-memory/repository evidence through
    the existing rigorous cohort core.

    This fixture deliberately has:
    - exact reproducible RAW lineage;
    - explicit NATIONAL offer reach;
    - stable provider identity;
    - NO admissible temporal evidence.

    Therefore the observation is eligible, passes lineage and reach, but MUST
    be excluded by temporal admission. No ordinary pricing cohort may appear.
    """

    stats = importlib.import_module(
        "scripts.build_pricing_statistics"
    )

    # Import/getattr inside the test so the intended RED is an execution failure,
    # not a collection/import failure.
    builder = getattr(
        stats,
        "build_runtime_pricing_statistics_from_objects",
    )

    observation_id = "1"
    source = "fixture_live_runtime"
    source_url = "https://example.test/soporte-remoto"
    raw_text = (
        "<html><body>"
        "Soporte remoto por hora con cobertura nacional $30000"
        "</body></html>"
    )
    digest = hashlib.sha256(
        raw_text.encode("utf-8")
    ).hexdigest()
    raw_document_id = f"sha256:{digest}"
    acquired_at = datetime(
        2026,
        9,
        4,
        12,
        0,
        tzinfo=timezone.utc,
    )

    raw_document = DocumentoRaw(
        source=source,
        source_record_id="fixture-page",
        source_url=source_url,
        retrieved_at=acquired_at,
        content_type="text/html",
        raw_content=raw_text,
        content_hash=digest,
        metadata={},
        storage_id=1,
    )
    repository = FakeRawRepository((raw_document,))

    row = {
        "observation_id": observation_id,
        "source": source,
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "currency": "ARS",
        "canonical_service": "SOPORTE_REMOTO",
        "province": "",
        "price_value": "30000",
        "economic_object_raw": (
            "Soporte remoto por hora con cobertura nacional"
        ),
        "extractor_version": "fixture-extractor-v1",
        "provider": "Fixture Provider",
    }

    reach_claim = SourceEconomicClaim(
        observation_id=observation_id,
        dimension="geographic_reach",
        value="NATIONAL",
        raw_basis="cobertura nacional",
        raw_document_id=raw_document_id,
        extraction_method=(
            SourceClaimMethod.SOURCE_TEXT_EXPLICIT
        ),
        provenance="fixture#service-reach",
    )

    evidence = OfferReachChargedScopeEvidence(
        observation_id=observation_id,
        lineage=EvidenceLineage(
            observation_id=observation_id,
            source_id=source,
            raw_document_id=raw_document_id,
            source_url=source_url,
            acquired_at=acquired_at.isoformat(),
            extractor_version="fixture-extractor-v1",
            provenance="sqlite:raw_documents/1",
            raw_document_path=None,
            raw_document_hash=digest,
            linkage_status="TRACEABLE_RAW",
            no_linkage_reason=None,
        ),
        claims=(reach_claim,),
    )

    source_registry = {
        source: {
            "source": source,
            "provider": "Fixture Provider",
        }
    }
    dimensions = derive_economic_dimensions_v2(
        row,
        source_registry,
        evidence.claims,
        raw_document_id=raw_document_id,
    )

    local_out = tmp_path / "local_runtime.csv"
    remote_out = tmp_path / "remote_runtime.csv"

    local, remote = builder(
        (row,),
        {observation_id: evidence},
        repository_root=tmp_path,
        local_out_path=local_out,
        remote_out_path=remote_out,
        service_reach_dimensions={
            observation_id: dimensions,
        },
        # Deliberately present-but-empty: temporal gate is enabled and the
        # observation has no admissible TemporalEvidence.
        temporal_evidence={},
        provider_dimensions={
            observation_id: dimensions,
        },
        raw_repository=repository,
    )

    assert local.eligible_before == 0
    assert local.admitted == 0
    assert local.cohorts == ()

    assert remote.eligible_before == 1
    assert remote.lineage_admitted == 1
    assert remote.reach_admitted == 1
    assert remote.temporal_admitted == 0
    assert remote.admitted == 0
    assert remote.excluded == 1
    assert remote.cohorts == ()

    assert len(remote.temporal_decisions) == 1
    assert remote.temporal_decisions[0].admitted is False
    assert (
        remote.temporal_decisions[0].exclusion_reason
        == "MISSING_TEMPORAL_PROVENANCE"
    )

    # A rigorous zero-cohort artifact is valid and auditable: headers exist,
    # but no weak/ordinary cohort row is emitted.
    assert local_out.is_file()
    assert remote_out.is_file()
    assert _csv_rows(local_out) == []
    assert _csv_rows(remote_out) == []

    header = remote_out.read_text(
        encoding="utf-8-sig"
    ).splitlines()[0]
    for required in (
        "provider_independence_version",
        "lineage_gate_version",
        "service_reach_gate_version",
        "temporal_gate_version",
        "temporal_state",
        "freshness_policy_version",
        "observation_ids",
    ):
        assert required in header
