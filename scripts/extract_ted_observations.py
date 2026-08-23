# ENKI_CLI_BOOTSTRAP_V1
try:
    from scripts._repo_bootstrap import activate_repo_root
except ModuleNotFoundError:
    from _repo_bootstrap import activate_repo_root

activate_repo_root(__file__)

import argparse
import json
from dataclasses import asdict
from typing import Any

from src.aplicacion.extractor_contrataciones_ted import ExtractorContratacionesTed, UNKNOWN
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)

COVERAGE_FIELDS = {
    "title": "title_raw",
    "description": "description_raw",
    "CPV": "classification_raw",
    "buyer": "buyer_raw",
    "supplier": "supplier_raw",
    "country": "country_raw",
    "publication_date": "published_at_raw",
    "economic_value": "value_raw",
    "currency": "currency_raw",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract deterministic procurement observations from TED raw documents."
    )
    parser.add_argument("--db", default="datos.db")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--extractor-version", default="ted-procurement-v1")
    args = parser.parse_args()

    repo = RepositorioSQLiteEvidencia(ruta_db=args.db)
    documentos = repo.listar_documentos_raw(source="ted", limit=args.limit)
    extractor = ExtractorContratacionesTed(extractor_version=args.extractor_version)
    resultado = extractor.extraer_lote(documentos, repo)
    observaciones = repo.listar_observaciones_contratacion(
        extractor_version=args.extractor_version
    )
    payload = {
        "result": asdict(resultado),
        "coverage": field_coverage(observaciones),
        "economic_value_coverage": economic_value_coverage(observaciones),
        "samples": sample_observations(observaciones, limit=10),
        "raw_documents": repo.contar_documentos_raw(source="ted"),
        "observations": repo.contar_observaciones_contratacion(
            extractor_version=args.extractor_version
        ),
    }
    print(json.dumps(payload, ensure_ascii=False))


def field_coverage(observaciones) -> dict[str, dict[str, int]]:
    total = len(observaciones)
    return {
        name: {"present": sum(_is_present(getattr(obs, attr)) for obs in observaciones), "total": total}
        for name, attr in COVERAGE_FIELDS.items()
    }


def economic_value_coverage(observaciones) -> dict[str, Any]:
    semantics: dict[str, int] = {}
    with_value = 0
    with_currency = 0
    for obs in observaciones:
        if _is_present(obs.value_raw):
            with_value += 1
        if _is_present(obs.currency_raw):
            with_currency += 1
        semantics[obs.value_semantics] = semantics.get(obs.value_semantics, 0) + 1
    return {
        "with_any_value": with_value,
        "with_currency": with_currency,
        "without_value": len(observaciones) - with_value,
        "value_semantics": semantics,
    }


def sample_observations(observaciones, limit: int) -> list[dict[str, Any]]:
    return [
        {
            "raw_identifier": obs.source_record_id,
            "title": _display(obs.title_raw),
            "CPV": obs.classification_raw,
            "buyer": _display(obs.buyer_raw),
            "supplier": _display(obs.supplier_raw),
            "economic_values": obs.value_raw,
            "currency": obs.currency_raw,
            "country": obs.country_raw,
        }
        for obs in observaciones[:limit]
    ]


def _is_present(value: Any) -> bool:
    return value not in (None, "", [], {}, UNKNOWN)


def _display(value: Any) -> Any:
    if isinstance(value, dict):
        eng = value.get("eng") or value.get("ENG")
        if isinstance(eng, list) and eng:
            return eng[0]
        if isinstance(eng, str):
            return eng
        for candidate in value.values():
            if isinstance(candidate, list) and candidate:
                return candidate[0]
            if isinstance(candidate, str):
                return candidate
    return value


if __name__ == "__main__":
    main()
