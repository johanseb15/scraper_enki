import argparse
import json
from dataclasses import asdict

from src.aplicacion.colector_usaspending import ColectorUSASpending
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia
from src.infraestructura.usaspending.cliente_busqueda import USASpendingClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect raw USASpending technology award records."
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--db", default="datos.db")
    parser.add_argument("--allow-insecure-tls", action="store_true")
    args = parser.parse_args()

    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")

    repo = RepositorioSQLiteEvidencia(ruta_db=args.db)
    collector = ColectorUSASpending(
        cliente=USASpendingClient(verify_tls=not args.allow_insecure_tls),
        repositorio=repo,
    )
    resultado = collector.colectar(limit=args.limit)
    print(json.dumps(asdict(resultado), ensure_ascii=False))


if __name__ == "__main__":
    main()
