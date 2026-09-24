import json
from datetime import datetime
from pathlib import Path

from src.dominio.evidencia import ConsultaUsuarioRaw


def load_observed_user_raw_corpus(
    path: Path,
) -> tuple[ConsultaUsuarioRaw, ...]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        records.append(
            ConsultaUsuarioRaw(
                source=row["source"],
                source_id=row["source_id"],
                source_url=row["source_url"],
                raw_text=row["raw_text"],
                language=row["language"],
                observed_at=datetime.fromisoformat(row["observed_at"]),
                metadata=row["metadata"],
            )
        )
    return tuple(records)
