from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.aplicacion.colector_precios_batch import (
    ExtractorPrecio,
    ResultadoBatchPricing,
    colectar_fuentes_pricing,
)
from src.aplicacion.pricing_source_registry import (
    cargar_fuentes_pricing_csv,
)
from src.aplicacion.puertos.repositorio_evidencia import (
    RepositorioEvidencia,
)
from src.aplicacion.semantic_normalization_live import (
    build_semantic_rows,
    write_semantic_csv,
)


class DownloaderPricing(Protocol):
    def descargar(self, url: str) -> str:
        ...


@dataclass(frozen=True)
class ResultadoPipelinePricingLive:
    acquisition: ResultadoBatchPricing
    semantic_rows: int
    frozen_rows_reused: int
    newly_classified: int
    db_path: Path
    semantic_path: Path
    local_stats_path: Path
    remote_stats_path: Path


def ejecutar_pipeline_pricing_live(
    *,
    sources_path: str | Path,
    db_path: str | Path,
    baseline_semantic_path: str | Path,
    semantic_out_path: str | Path,
    local_stats_out_path: str | Path,
    remote_stats_out_path: str | Path,
    repositorio: RepositorioEvidencia,
    downloader: DownloaderPricing,
    extractor: ExtractorPrecio,
) -> ResultadoPipelinePricingLive:
    """Run acquisition -> semantic bridge without depending on infrastructure.

    Infrastructure adapters (SQLite, HTTP, extractor implementation) are
    injected by the composition root / CLI.
    """
    sources_path = Path(sources_path)
    db_path = Path(db_path)
    baseline_semantic_path = Path(baseline_semantic_path)
    semantic_out_path = Path(semantic_out_path)
    local_stats_out_path = Path(local_stats_out_path)
    remote_stats_out_path = Path(remote_stats_out_path)

    semantic_out_path.parent.mkdir(parents=True, exist_ok=True)
    local_stats_out_path.parent.mkdir(parents=True, exist_ok=True)
    remote_stats_out_path.parent.mkdir(parents=True, exist_ok=True)

    fuentes = cargar_fuentes_pricing_csv(sources_path)

    acquisition = colectar_fuentes_pricing(
        fuentes,
        repositorio=repositorio,
        downloader=downloader,
        extractor=extractor,
    )

    if acquisition.sources_succeeded == 0:
        raise RuntimeError(
            "Live pricing acquisition produced zero successful sources"
        )

    rows, reused, newly_classified = build_semantic_rows(
        db_path,
        baseline_path=baseline_semantic_path,
    )
    write_semantic_csv(semantic_out_path, rows)

    return ResultadoPipelinePricingLive(
        acquisition=acquisition,
        semantic_rows=len(rows),
        frozen_rows_reused=reused,
        newly_classified=newly_classified,
        db_path=db_path,
        semantic_path=semantic_out_path,
        local_stats_path=local_stats_out_path,
        remote_stats_path=remote_stats_out_path,
    )
