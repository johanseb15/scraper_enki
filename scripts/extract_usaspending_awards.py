import argparse
import json
from dataclasses import asdict

from src.aplicacion.extractor_usaspending_awards import ExtractorUSASpendingAwards
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract deterministic USASpending award observations from raw documents."
    )
    parser.add_argument("--db", default="datos.db")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--extractor-version", default="usaspending_award_v1")
    args = parser.parse_args()

    repo = RepositorioSQLiteEvidencia(ruta_db=args.db)
    documentos = repo.listar_documentos_raw(source="usaspending", limit=args.limit)
    extractor = ExtractorUSASpendingAwards(extractor_version=args.extractor_version)
    resultado = extractor.extraer_lote(documentos, repo)
    print(json.dumps(asdict(resultado), ensure_ascii=False))


if __name__ == "__main__":
    main()
