import argparse
import json

from src.aplicacion.importador_evidencia import ImportadorEvidencia
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Importa evidencia raw desde archivos JSONL."
    )
    parser.add_argument("kind", choices=("language", "sources"))
    parser.add_argument("path")
    parser.add_argument("--db", default="datos.db")
    args = parser.parse_args()

    repo = RepositorioSQLiteEvidencia(ruta_db=args.db)
    importador = ImportadorEvidencia(repo)
    if args.kind == "language":
        resultado = importador.importar_lenguaje_jsonl(args.path)
    else:
        resultado = importador.importar_fuentes_jsonl(args.path)

    print(
        json.dumps(
            {
                "accepted": resultado.accepted,
                "rejected": resultado.rejected,
                "duplicate": resultado.duplicate,
                "rejected_records": [
                    {
                        "line_number": record.line_number,
                        "reason": record.reason,
                    }
                    for record in resultado.rejected_records
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
