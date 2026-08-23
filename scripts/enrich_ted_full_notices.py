# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json
from dataclasses import asdict

from src.aplicacion.colector_ted_full_notices import ColectorTedFullNotices
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia
from src.infraestructura.ted.cliente_full_notice import TedFullNoticeClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch official TED full notice documents for existing search records."
    )
    parser.add_argument("--db", default="datos.db")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--allow-insecure-tls", action="store_true")
    args = parser.parse_args()

    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")

    repo = RepositorioSQLiteEvidencia(ruta_db=args.db)
    documentos = repo.listar_documentos_raw(source="ted", limit=args.limit)
    collector = ColectorTedFullNotices(
        cliente=TedFullNoticeClient(verify_tls=not args.allow_insecure_tls),
        repositorio=repo,
    )
    resultado = collector.enriquecer(documentos)
    payload = {
        "result": asdict(resultado),
        "db_counts": {
            "ted_search_documents": repo.contar_documentos_raw(source="ted"),
            "ted_full_notice_documents": repo.contar_documentos_raw(
                source="ted_full_notice"
            ),
        },
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
