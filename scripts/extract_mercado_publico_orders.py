# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json
from dataclasses import asdict

from src.aplicacion.extractor_mercado_publico_ordenes import ExtractorMercadoPublicoOrdenes
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract observed Mercado Publico purchase orders and line items from raw documents.")
    parser.add_argument("--db", default="datos.db")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--extractor-version", default="mercado_publico_purchase_order_v1")
    args = parser.parse_args()

    repo = RepositorioSQLiteEvidencia(ruta_db=args.db)
    documentos = repo.listar_documentos_raw(source="mercado_publico_cl", limit=args.limit)
    resultado = ExtractorMercadoPublicoOrdenes(args.extractor_version).extraer_lote(documentos, repo)
    print(json.dumps(asdict(resultado), ensure_ascii=False))


if __name__ == "__main__":
    main()
