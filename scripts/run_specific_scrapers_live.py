from __future__ import annotations

# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from src.infraestructura.scrapers.baires_cloud import BairesCloudScraper
from src.infraestructura.scrapers.cirowhite import CiroWhiteScraper
from src.infraestructura.scrapers.compragamer_scraper import CompraGamerScraper
from src.infraestructura.scrapers.dmr import DMRScraper
from src.infraestructura.scrapers.reed import ReedScraper
from src.infraestructura.scrapers.venex import VenexScraper
from src.infraestructura.scrapers.vida_informatica import VidaInformaticaScraper
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import (
    RepositorioSQLiteOfertas,
)
from src.pipeline import PipelineOfertas


SCHEMA_VERSION = "specific-live-scrapers-v1"


def construir_grupos_scrapers() -> dict[str, list[Any]]:
    """Build the explicit live catalog without mixing services and goods."""
    return {
        "local_services": [
            BairesCloudScraper(),
            VidaInformaticaScraper(),
            CiroWhiteScraper(),
            DMRScraper(),
            ReedScraper(),
        ],
        "reference_products": [
            VenexScraper(),
            CompraGamerScraper(),
        ],
    }


def ejecutar_scrapers_especificos(
    *,
    out_dir: str | Path,
    run_id: str,
    pipeline_type=PipelineOfertas,
    repository_type=RepositorioSQLiteOfertas,
) -> Path:
    """Run every specific scraper and persist isolated diagnostic databases.

    These adapters do not preserve the complete source document. Their output
    is therefore useful for scraper health and candidate discovery, but it is
    not admitted automatically into the RAW-first evidence pipeline.
    """
    run_dir = Path(out_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnostic_only": True,
        "admission_reason": (
            "Specific legacy scrapers do not preserve complete RAW source "
            "documents; outputs require evidence admission before comparison."
        ),
        "groups": {},
    }

    for group_name, scrapers in construir_grupos_scrapers().items():
        db_path = run_dir / f"{group_name}.db"
        pipeline = pipeline_type(
            scrapers=scrapers,
            repositorio=repository_type(db_path),
        )
        rows = pipeline.ejecutar()
        manifest["groups"][group_name] = {
            "database": db_path.name,
            "sources_attempted": len(scrapers),
            "sources_succeeded": list(pipeline.metricas.exitosos),
            "sources_failed": list(pipeline.metricas.fallidos),
            "offers_processed": len(rows),
        }

    manifest_path = run_dir / "specific_scraper_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run every Enki-specific scraper into isolated diagnostic stores."
        )
    )
    parser.add_argument("--out-dir", default="data/live_specific")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ejecutar_scrapers_especificos(
        out_dir=args.out_dir,
        run_id=run_id,
    )

    manifest = json.loads(
        (run_dir / "specific_scraper_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    print("ENKI SPECIFIC LIVE SCRAPERS")
    print("===========================")
    print(f"Run ID: {run_id}")
    for group_name, result in manifest["groups"].items():
        print(
            f"{group_name}: {result['offers_processed']} offers; "
            f"{len(result['sources_succeeded'])} succeeded; "
            f"{len(result['sources_failed'])} failed"
        )
    print(f"Manifest: {run_dir / 'specific_scraper_manifest.json'}")


if __name__ == "__main__":
    main()
