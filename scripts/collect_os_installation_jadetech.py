# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json

from src.aplicacion.colector_precios_os_jadetech import ColectorPreciosOSJadetech
from src.infraestructura.downloader import descargar_html
from src.infraestructura.scrapers.jadetech_os_parser import extraer_observaciones_jadetech_os
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


class RequestsDownloader:
    def descargar(self, url: str) -> str:
        return descargar_html(url)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect commercial OS installation/formateo evidence from Jadetech."
    )
    parser.add_argument("--db", default="datos.db")
    args = parser.parse_args()
    repo = RepositorioSQLiteEvidencia(args.db)
    collector = ColectorPreciosOSJadetech(
        repositorio=repo,
        downloader=RequestsDownloader(),
        parser_observaciones=extraer_observaciones_jadetech_os,
    )
    resultado = collector.colectar()
    print(json.dumps(resultado.__dict__, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
