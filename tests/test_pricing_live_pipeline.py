from dataclasses import dataclass
from pathlib import Path

import pytest

import src.aplicacion.pricing_live_pipeline as pipeline


@dataclass(frozen=True)
class FakeResult:
    sources_attempted: int = 1
    sources_succeeded: int = 1
    sources_failed: int = 0
    raw_docs_acquired: int = 1
    raw_docs_duplicate: int = 0
    observations_extracted: int = 1
    observations_duplicate: int = 0
    exact_prices: int = 1
    failures: tuple = ()


class FakeDownloader:
    def descargar(self, url: str) -> str:
        return "<html></html>"


class FakeRepo:
    pass


def fake_extractor(*args, **kwargs):
    return []


def test_pipeline_orchestrates_acquisition_and_semantics(tmp_path, monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "cargar_fuentes_pricing_csv",
        lambda path: ["source"],
    )
    monkeypatch.setattr(
        pipeline,
        "colectar_fuentes_pricing",
        lambda *args, **kwargs: FakeResult(),
    )
    monkeypatch.setattr(
        pipeline,
        "build_semantic_rows",
        lambda *args, **kwargs: ([{"x": "y"}], 10, 1),
    )

    written = {}
    monkeypatch.setattr(
        pipeline,
        "write_semantic_csv",
        lambda path, rows: written.update(path=Path(path), rows=rows),
    )

    result = pipeline.ejecutar_pipeline_pricing_live(
        sources_path=tmp_path / "sources.csv",
        db_path=tmp_path / "pricing.db",
        baseline_semantic_path=tmp_path / "baseline.csv",
        semantic_out_path=tmp_path / "semantic.csv",
        local_stats_out_path=tmp_path / "local.csv",
        remote_stats_out_path=tmp_path / "remote.csv",
        repositorio=FakeRepo(),
        downloader=FakeDownloader(),
        extractor=fake_extractor,
    )

    assert result.semantic_rows == 1
    assert result.frozen_rows_reused == 10
    assert result.newly_classified == 1
    assert written["path"] == tmp_path / "semantic.csv"


def test_pipeline_rejects_zero_successful_sources(tmp_path, monkeypatch):
    bad = FakeResult(
        sources_attempted=2,
        sources_succeeded=0,
        sources_failed=2,
        raw_docs_acquired=0,
        observations_extracted=0,
        exact_prices=0,
    )
    monkeypatch.setattr(
        pipeline,
        "cargar_fuentes_pricing_csv",
        lambda path: ["a", "b"],
    )
    monkeypatch.setattr(
        pipeline,
        "colectar_fuentes_pricing",
        lambda *args, **kwargs: bad,
    )

    with pytest.raises(RuntimeError, match="zero successful sources"):
        pipeline.ejecutar_pipeline_pricing_live(
            sources_path=tmp_path / "sources.csv",
            db_path=tmp_path / "pricing.db",
            baseline_semantic_path=tmp_path / "baseline.csv",
            semantic_out_path=tmp_path / "semantic.csv",
            local_stats_out_path=tmp_path / "local.csv",
            remote_stats_out_path=tmp_path / "remote.csv",
            repositorio=FakeRepo(),
            downloader=FakeDownloader(),
            extractor=fake_extractor,
        )
