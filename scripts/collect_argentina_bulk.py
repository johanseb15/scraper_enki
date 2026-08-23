# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json
from dataclasses import asdict

from src.aplicacion.colector_argentina_bulk import ColectorArgentinaBulk, RecursoArgentinaBulk
from src.infraestructura.datos_argentina.cliente import DatosArgentinaClient
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import RepositorioSQLiteEvidencia

CORE_RESOURCE_NAMES = {
    "Convocatorias 2016 - 2026",
    "Adjudicaciones 2016 - 2026",
    "SIPRO 2016-2026",
    "Cat?logo de Bienes y Servicios (SIByS)",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk ingest official Argentina COMPR.AR CSV resources from datos.gob.ar.")
    parser.add_argument("--db", default="enki_argentina_procurement.db")
    parser.add_argument("--dataset-id", default="sistema-de-contrataciones-electronicas")
    parser.add_argument("--all-csv", action="store_true", help="Download all CSV resources, including historical/superseded yearly files.")
    parser.add_argument("--allow-insecure-tls", action="store_true")
    args = parser.parse_args()

    client = DatosArgentinaClient(verify_tls=not args.allow_insecure_tls)
    resources = client.recursos_dataset(args.dataset_id)
    selected = resources if args.all_csv else [resource for resource in resources if resource.name in CORE_RESOURCE_NAMES or resource.resource_type == "sibys"]
    repo = RepositorioSQLiteEvidencia(args.db)
    result = ColectorArgentinaBulk(client, repo).colectar(selected)
    payload = {"selected_resources": [asdict(resource) for resource in selected], "result": asdict(result)}
    payload["result"]["rejected_rows_sample"] = payload["result"].pop("rejected_rows")[:20]
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
