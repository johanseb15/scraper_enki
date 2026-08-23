# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json
from dataclasses import asdict

from src.aplicacion.colector_mercado_publico import ColectorMercadoPublicoCL
from src.infraestructura.mercado_publico.cliente import MercadoPublicoClient
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Mercado Publico Chile purchase orders.")
    parser.add_argument("--fecha", required=True, help="Fecha ddmmaaaa")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--estado", default="todos")
    parser.add_argument("--db", default="datos.db")
    parser.add_argument("--allow-insecure-tls", action="store_true")
    parser.add_argument("--request-interval-seconds", type=float, default=0.0)
    parser.add_argument("--retries", type=int, default=5)
    args = parser.parse_args()

    repo = RepositorioSQLiteEvidencia(ruta_db=args.db)
    collector = ColectorMercadoPublicoCL(
        cliente=MercadoPublicoClient(
            verify_tls=not args.allow_insecure_tls,
            request_interval_seconds=args.request_interval_seconds,
            retries=args.retries,
        ),
        repositorio=repo,
    )
    resultado = collector.colectar_ordenes(
        fecha=args.fecha, estado=args.estado, limit=args.limit
    )
    print(json.dumps(asdict(resultado), ensure_ascii=False))


if __name__ == "__main__":
    main()
