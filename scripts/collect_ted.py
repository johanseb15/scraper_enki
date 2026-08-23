# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json
from dataclasses import asdict

from src.aplicacion.colector_documentos_raw import ColectorDocumentosRaw
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)
from src.infraestructura.ted.cliente_busqueda import TedPublicSearchClient

DEFAULT_TED_QUERY = "classification-cpv = 72000000"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect raw public procurement documents from TED."
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--db", default="datos.db")
    parser.add_argument("--query", default=DEFAULT_TED_QUERY)
    parser.add_argument("--allow-insecure-tls", action="store_true")
    args = parser.parse_args()

    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")

    repo = RepositorioSQLiteEvidencia(ruta_db=args.db)
    collector = ColectorDocumentosRaw(
        cliente=TedPublicSearchClient(verify_tls=not args.allow_insecure_tls),
        repositorio=repo,
        fuente="ted",
    )
    resultado = collector.colectar(query=args.query, limit=args.limit)
    print(json.dumps(asdict(resultado), ensure_ascii=False))


if __name__ == "__main__":
    main()
