import csv
import importlib
import sys
from types import SimpleNamespace


def _write_semantic(path):
    fields = (
        "observation_id",
        "source",
        "province",
        "city",
        "economic_object_raw",
        "price_value",
        "currency",
        "semantic_role",
        "market_scope",
        "matched_services",
        "canonical_service",
        "comparability_key",
        "original_comparable_status",
        "extractor_version",
    )
    row = {
        "observation_id": "1",
        "source": "fixture_live",
        "province": "",
        "city": "",
        "economic_object_raw": "Soporte remoto por hora",
        "price_value": "30000",
        "currency": "ARS",
        "semantic_role": "SINGLE_SERVICE",
        "market_scope": "REMOTE_NATIONAL_SERVICE",
        "matched_services": "SOPORTE_REMOTO",
        "canonical_service": "SOPORTE_REMOTO",
        "comparability_key": "AR::SOPORTE_REMOTO",
        "original_comparable_status": "CANDIDATE",
        "extractor_version": "fixture-extractor-v1",
    }

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerow(row)


def test_live_runner_passes_projected_temporal_evidence_to_rigorous_builder(
    tmp_path,
    monkeypatch,
):
    """
    Once live temporal evidence has a storage-neutral projection, the live
    composition root must pass that exact map to the rigorous runtime builder.

    An empty literal {} is no longer acceptable because it discards real,
    auditable HISTORICAL_REPRODUCIBLE price-time evidence.
    """

    runner = importlib.import_module(
        "scripts.run_pricing_live_pipeline"
    )

    out_dir = tmp_path / "live"
    sources = tmp_path / "sources.csv"
    baseline = tmp_path / "baseline.csv"

    # Argument targets only. Registry and acquisition are patched below.
    sources.write_text(
        "placeholder\n",
        encoding="utf-8",
    )
    baseline.write_text(
        "placeholder\n",
        encoding="utf-8",
    )

    fake_repo = object()

    monkeypatch.setattr(
        runner,
        "RepositorioSQLiteEvidencia",
        lambda path: fake_repo,
    )
    monkeypatch.setattr(
        runner,
        "DownloaderHTTP",
        lambda timeout=20: object(),
    )

    def fake_pipeline(**kwargs):
        _write_semantic(
            kwargs["semantic_out_path"]
        )

        acquisition = SimpleNamespace(
            sources_attempted=1,
            sources_succeeded=1,
            sources_failed=0,
            raw_docs_acquired=1,
            raw_docs_duplicate=0,
            observations_extracted=1,
            observations_duplicate=0,
            exact_prices=1,
            failures=(),
        )

        return SimpleNamespace(
            acquisition=acquisition,
            semantic_rows=1,
            frozen_rows_reused=0,
            newly_classified=1,
            db_path=kwargs["db_path"],
            semantic_path=kwargs["semantic_out_path"],
            local_stats_path=kwargs["local_stats_out_path"],
            remote_stats_path=kwargs["remote_stats_out_path"],
        )

    monkeypatch.setattr(
        runner,
        "ejecutar_pipeline_pricing_live",
        fake_pipeline,
    )

    monkeypatch.setattr(
        runner,
        "cargar_registry_pricing_csv",
        lambda path: (
            SimpleNamespace(
                source="fixture_live",
                provider="Fixture Provider",
                url="https://example.test",
                province="CABA",
                city="CABA",
                discovery_status="VERIFIED",
                price_visibility="PRICE_VISIBLE",
                source_kind="PROVIDER",
                notes="",
            ),
        ),
    )

    offer_evidence = SimpleNamespace(
        claims=(),
        lineage=SimpleNamespace(
            raw_document_id="sha256:fixture",
        ),
    )

    monkeypatch.setattr(
        runner,
        "build_live_offer_evidence",
        lambda *, repository: {
            "1": offer_evidence
        },
    )

    dimension = object()

    monkeypatch.setattr(
        runner,
        "derive_economic_dimensions_v2",
        lambda *args, **kwargs: dimension,
    )

    temporal_projection = {
        "1": SimpleNamespace(
            observation_id="1",
            temporal_state="HISTORICAL_REPRODUCIBLE",
            freshness_policy_known=False,
        )
    }
    temporal_calls = []

    def fake_temporal_builder(*, repository):
        temporal_calls.append(repository)
        return temporal_projection

    # raising=False keeps this as a causal composition RED while the runner
    # does not yet import the production bridge.
    monkeypatch.setattr(
        runner,
        "build_live_temporal_evidence",
        fake_temporal_builder,
        raising=False,
    )

    rigorous_calls = []

    def rigorous_builder(
        rows,
        evidence_by_observation,
        **kwargs,
    ):
        rigorous_calls.append(
            (
                tuple(rows),
                evidence_by_observation,
                kwargs,
            )
        )
        empty = SimpleNamespace(
            cohorts=()
        )
        return empty, empty

    monkeypatch.setattr(
        runner,
        "build_runtime_pricing_statistics_from_objects",
        rigorous_builder,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pricing_live_pipeline.py",
            "--sources",
            str(sources),
            "--baseline",
            str(baseline),
            "--out-dir",
            str(out_dir),
            "--run-id",
            "fixture-run",
        ],
    )

    runner.main()

    assert temporal_calls == [
        fake_repo
    ]
    assert len(rigorous_calls) == 1

    _, _, kwargs = rigorous_calls[0]

    assert (
        kwargs["temporal_evidence"]
        is temporal_projection
    )
