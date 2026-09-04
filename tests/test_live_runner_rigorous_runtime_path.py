import csv
import importlib
import sys
from types import SimpleNamespace


def _write_sources(path):
    path.write_text(
        "source,provider,url,province,city,discovery_status,"
        "price_visibility,source_kind,notes\n"
        "fixture_live,Fixture Provider,https://example.test,"
        "CABA,CABA,VERIFIED,PRICE_VISIBLE,PROVIDER,\n",
        encoding="utf-8",
    )


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
        "economic_object_raw": (
            "Soporte remoto por hora con cobertura nacional"
        ),
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
    path.parent.mkdir(parents=True, exist_ok=True)
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


def test_live_runner_uses_rigorous_objects_path_and_never_ordinary_stats(
    tmp_path,
    monkeypatch,
):
    """
    The live composition root must never fall back to ordinary semantic-only
    pricing statistics.

    This test isolates the post-acquisition boundary:
    acquisition/semantic output succeeds, live evidence and dimensions are
    available, temporal input is supplied to the rigorous builder, and the
    ordinary builder is a tripwire.
    """

    runner = importlib.import_module(
        "scripts.run_pricing_live_pipeline"
    )

    sources = tmp_path / "sources.csv"
    baseline = tmp_path / "baseline.csv"
    out_dir = tmp_path / "live"

    _write_sources(sources)
    baseline.write_text(
        "source,economic_object_raw,price_value,currency\n",
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

    weak_calls = []

    def weak_builder(*args, **kwargs):
        weak_calls.append((args, kwargs))
        raise AssertionError(
            "WEAK_PRICING_STATISTICS_PATH_INVOKED"
        )

    # Current code owns this attribute. raising=False also keeps the test
    # valid once the import is removed: any accidental fallback still trips.
    monkeypatch.setattr(
        runner,
        "build_pricing_statistics",
        weak_builder,
        raising=False,
    )

    evidence = SimpleNamespace(
        claims=(),
        lineage=SimpleNamespace(
            raw_document_id="sha256:fixture",
        ),
    )
    dimension = object()

    monkeypatch.setattr(
        runner,
        "build_live_offer_evidence",
        lambda *, repository: {"1": evidence},
        raising=False,
    )
    monkeypatch.setattr(
        runner,
        "derive_economic_dimensions_v2",
        lambda *args, **kwargs: dimension,
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
        empty = SimpleNamespace(cohorts=())
        return empty, empty

    monkeypatch.setattr(
        runner,
        "build_runtime_pricing_statistics_from_objects",
        rigorous_builder,
        raising=False,
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

    assert weak_calls == []
    assert len(rigorous_calls) == 1

    rows, evidence_arg, kwargs = rigorous_calls[0]

    assert len(rows) == 1
    assert rows[0]["observation_id"] == "1"
    assert evidence_arg == {"1": evidence}

    # None would disable these gates in build_runtime_cohort_rows.
    assert kwargs["service_reach_dimensions"] is not None
    assert kwargs["temporal_evidence"] is not None
    assert kwargs["provider_dimensions"] is not None

    assert kwargs["raw_repository"] is fake_repo
