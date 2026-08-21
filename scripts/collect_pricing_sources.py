from __future__ import annotations

import argparse
from pathlib import Path

from src.aplicacion.colector_precios_batch import (
    colectar_fuentes_pricing,
)
from src.aplicacion.pricing_source_registry import (
    cargar_fuentes_pricing_csv,
)
from src.infraestructura.downloader import (
    descargar_html,
)
from src.infraestructura.http_tls import (
    crear_session_system_trust,
)
from src.infraestructura.scrapers.generic_price_extractor import (
    extraer_observaciones_precio_genericas,
)
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


class DownloaderHTTP:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = crear_session_system_trust()

    def descargar(self, url: str) -> str:
        return descargar_html(
            url,
            timeout=self.timeout,
            session=self.session,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Adquiere automáticamente evidencia "
            "de precios desde el source registry."
        )
    )

    parser.add_argument(
        "--sources",
        type=Path,
        default=Path(
            "data/pricing_sources.csv"
        ),
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=Path(
            "data/enki_pricing.db"
        ),
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
    )

    args = parser.parse_args()

    fuentes = cargar_fuentes_pricing_csv(
        args.sources
    )

    args.db.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    repo = RepositorioSQLiteEvidencia(
        str(args.db)
    )

    resultado = colectar_fuentes_pricing(
        fuentes,
        repositorio=repo,
        downloader=DownloaderHTTP(
            timeout=args.timeout
        ),
        extractor=extraer_observaciones_precio_genericas,
    )

    print()
    print("ENKI PRICING ACQUISITION")
    print("========================")
    print(
        f"Sources attempted:       "
        f"{resultado.sources_attempted}"
    )
    print(
        f"Sources succeeded:       "
        f"{resultado.sources_succeeded}"
    )
    print(
        f"Sources failed:          "
        f"{resultado.sources_failed}"
    )
    print(
        f"Raw docs acquired:       "
        f"{resultado.raw_docs_acquired}"
    )
    print(
        f"Raw docs duplicate:      "
        f"{resultado.raw_docs_duplicate}"
    )
    print(
        f"Observations extracted:  "
        f"{resultado.observations_extracted}"
    )
    print(
        f"Observations duplicate:  "
        f"{resultado.observations_duplicate}"
    )
    print(
        f"Exact prices detected:   "
        f"{resultado.exact_prices}"
    )

    if resultado.failures:
        print()
        print("FAILURES")
        print("--------")

        for failure in resultado.failures:
            print(
                f"{failure.source} [{failure.error_type}]: "
                f"{failure.error}"
            )


if __name__ == "__main__":
    main()
