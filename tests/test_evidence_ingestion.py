import json

from src.aplicacion.importador_evidencia import ImportadorEvidencia
from src.infraestructura.sqlite.repositorio_sqlite_evidencia import (
    RepositorioSQLiteEvidencia,
)


def _write_jsonl(path, records):
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records),
        encoding="utf-8",
    )


def test_importa_un_registro_de_lenguaje(tmp_path):
    ruta = tmp_path / "language.jsonl"
    raw_text = "me quieren cobrar 350.000 por mes\npor soporte para 15 PCs."
    _write_jsonl(
        ruta,
        [
            {
                "source": "x",
                "source_id": "post-1",
                "source_url": "https://example.test/post-1",
                "raw_text": raw_text,
                "language": "es",
                "observed_at": "2026-08-10T13:00:00Z",
                "metadata": {"role": "BUYER"},
            }
        ],
    )
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))

    resultado = ImportadorEvidencia(repo).importar_lenguaje_jsonl(ruta)

    assert resultado.accepted == 1
    assert resultado.rejected == 0
    assert resultado.duplicate == 0
    assert repo.contar_lenguaje() == 1


def test_importar_lenguaje_dos_veces_no_duplica(tmp_path):
    ruta = tmp_path / "language.jsonl"
    _write_jsonl(
        ruta,
        [
            {
                "source": "reddit",
                "source_id": "abc123",
                "source_url": "https://example.test/r/abc123",
                "raw_text": "client says I'm too expensive",
                "language": "en",
                "observed_at": "2026-08-10T13:00:00Z",
                "metadata": {},
            }
        ],
    )
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))
    importador = ImportadorEvidencia(repo)

    importador.importar_lenguaje_jsonl(ruta)
    resultado = importador.importar_lenguaje_jsonl(ruta)

    assert resultado.accepted == 0
    assert resultado.duplicate == 1
    assert repo.contar_lenguaje(source="reddit", language="en") == 1


def test_preserva_raw_text_exactamente(tmp_path):
    ruta = tmp_path / "language.jsonl"
    raw_text = "  quoted me 90k\n\nis this too much?  "
    _write_jsonl(
        ruta,
        [
            {
                "source": "x",
                "source_id": "raw-1",
                "source_url": "https://example.test/raw-1",
                "raw_text": raw_text,
                "language": "en",
                "observed_at": "2026-08-10T13:00:00Z",
                "metadata": {},
            }
        ],
    )
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))

    ImportadorEvidencia(repo).importar_lenguaje_jsonl(ruta)

    registros = repo.listar_lenguaje(source="x", language="en")
    assert registros[0].raw_text == raw_text


def test_importa_fuente_candidata(tmp_path):
    ruta = tmp_path / "sources.jsonl"
    _write_jsonl(
        ruta,
        [
            {
                "name": "r/msp",
                "url": "https://reddit.com/r/msp",
                "source_type": "community",
                "country": "US",
                "language": "en",
                "acquisition_method": "manual_seed",
                "metadata": {"notes": "provider language"},
            }
        ],
    )
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))

    resultado = ImportadorEvidencia(repo).importar_fuentes_jsonl(ruta)

    assert resultado.accepted == 1
    assert repo.contar_fuentes() == 1
    assert repo.listar_fuentes()[0].status == "CANDIDATE"


def test_registro_invalido_no_destruye_batch(tmp_path):
    ruta = tmp_path / "language.jsonl"
    ruta.write_text(
        "\n".join(
            [
                '{"source": "x", "source_id": "bad"}',
                json.dumps(
                    {
                        "source": "x",
                        "source_id": "good",
                        "source_url": "https://example.test/good",
                        "raw_text": "is this quote too high?",
                        "language": "en",
                        "observed_at": "2026-08-10T13:00:00Z",
                        "metadata": {},
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    repo = RepositorioSQLiteEvidencia(ruta_db=str(tmp_path / "evidence.db"))

    resultado = ImportadorEvidencia(repo).importar_lenguaje_jsonl(ruta)

    assert resultado.accepted == 1
    assert resultado.rejected == 1
    assert resultado.rejected_records[0].line_number == 1
    assert repo.contar_lenguaje() == 1
