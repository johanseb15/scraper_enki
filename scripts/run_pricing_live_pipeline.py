from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from scripts.build_pricing_statistics import build_pricing_statistics
from src.aplicacion.pricing_live_pipeline import ejecutar_pipeline_pricing_live
from src.infraestructura.downloader import descargar_html
from src.infraestructura.http_tls import crear_session_system_trust
from src.infraestructura.scrapers.generic_price_extractor import (
    extraer_observaciones_precio_genericas,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


class DownloaderHTTP:
    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = crear_session_system_trust()

    def descargar(self, url: str) -> str:
        return descargar_html(url, timeout=self.timeout, session=self.session)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Enki live pricing pipeline: acquisition -> semantic normalization "
            "-> pricing cohorts."
        )
    )
    ap.add_argument("--sources", default="data/pricing_sources.csv")
    ap.add_argument("--baseline", default="data/semantic_normalization_v4.csv")
    ap.add_argument("--out-dir", default="data/live")
    ap.add_argument("--run-id")
    ap.add_argument("--timeout", type=int, default=20)
    args = ap.parse_args()

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    db = out_dir / "enki_pricing.db"
    semantic = out_dir / "semantic_normalization.csv"
    local_stats = out_dir / "local_pricing_stats.csv"
    remote_stats = out_dir / "remote_pricing_stats.csv"

    repo = RepositorioSQLiteEvidencia(str(db))

    result = ejecutar_pipeline_pricing_live(
        sources_path=args.sources,
        db_path=db,
        baseline_semantic_path=args.baseline,
        semantic_out_path=semantic,
        local_stats_out_path=local_stats,
        remote_stats_out_path=remote_stats,
        repositorio=repo,
        downloader=DownloaderHTTP(timeout=args.timeout),
        extractor=extraer_observaciones_precio_genericas,
    )

    local, remote = build_pricing_statistics(
        semantic,
        local_out_path=local_stats,
        remote_out_path=remote_stats,
    )

    a = result.acquisition

    print()
    print("ENKI PRICING LIVE PIPELINE v1.1")
    print("===============================")
    print(f"Run ID:                 {run_id}")
    print(f"Sources attempted:      {a.sources_attempted}")
    print(f"Sources succeeded:      {a.sources_succeeded}")
    print(f"Sources failed:         {a.sources_failed}")
    print(f"Raw docs acquired:      {a.raw_docs_acquired}")
    print(f"Raw docs duplicate:     {a.raw_docs_duplicate}")
    print(f"Observations extracted: {a.observations_extracted}")
    print(f"Obs. duplicate:         {a.observations_duplicate}")
    print(f"Exact prices:           {a.exact_prices}")
    print(f"Semantic rows:          {result.semantic_rows}")
    print(f"Frozen v4 reused:       {result.frozen_rows_reused}")
    print(f"Newly classified:       {result.newly_classified}")
    print(f"Local cohorts:          {len(local)}")
    print(f"Remote cohorts:         {len(remote)}")
    print()
    print(f"DB:           {db}")
    print(f"Semantic:     {semantic}")
    print(f"Local stats:  {local_stats}")
    print(f"Remote stats: {remote_stats}")

    if a.failures:
        print()
        print("SOURCE FAILURES")
        print("---------------")
        for failure in a.failures:
            print(f"{failure.source} [{failure.error_type}]: {failure.error}")


if __name__ == "__main__":
    main()
