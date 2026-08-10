import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.aplicacion.puertos.repositorio_evidencia import RepositorioEvidencia
from src.dominio.evidencia import ConsultaUsuarioRaw, FuenteCandidata


@dataclass(frozen=True)
class RegistroRechazado:
    line_number: int
    reason: str


@dataclass
class ResultadoImportacion:
    accepted: int = 0
    rejected: int = 0
    duplicate: int = 0
    rejected_records: list[RegistroRechazado] = field(default_factory=list)


class ImportadorEvidencia:
    def __init__(self, repositorio: RepositorioEvidencia):
        self.repositorio = repositorio

    def importar_lenguaje_jsonl(self, ruta: str | Path) -> ResultadoImportacion:
        return self._importar_jsonl(ruta, self._importar_registro_lenguaje)

    def importar_fuentes_jsonl(self, ruta: str | Path) -> ResultadoImportacion:
        return self._importar_jsonl(ruta, self._importar_fuente)

    def _importar_jsonl(self, ruta: str | Path, handler) -> ResultadoImportacion:
        resultado = ResultadoImportacion()
        for line_number, line in enumerate(Path(ruta).read_text(encoding="utf-8-sig").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                inserted = handler(payload)
            except (ValueError, TypeError, KeyError) as exc:
                resultado.rejected += 1
                resultado.rejected_records.append(
                    RegistroRechazado(line_number=line_number, reason=str(exc))
                )
                continue

            if inserted:
                resultado.accepted += 1
            else:
                resultado.duplicate += 1
        return resultado

    def _importar_registro_lenguaje(self, payload: dict[str, Any]) -> bool:
        raw_text = self._required_non_empty(payload, "raw_text")
        source = self._required_non_empty(payload, "source")
        source_url = self._required_non_empty(payload, "source_url")
        language = self._required_non_empty(payload, "language")
        observed_at = self._parse_datetime(self._required_non_empty(payload, "observed_at"))
        source_id = str(payload.get("source_id") or "").strip()
        if not source_id:
            source_id = self._stable_hash(source=source, source_url=source_url, raw_text=raw_text)

        metadata = payload.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("metadata debe ser un objeto")

        return self.repositorio.guardar_lenguaje(
            ConsultaUsuarioRaw(
                source=source,
                source_id=source_id,
                source_url=source_url,
                raw_text=raw_text,
                language=language,
                observed_at=observed_at,
                metadata=metadata,
            )
        )

    def _importar_fuente(self, payload: dict[str, Any]) -> bool:
        metadata = payload.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("metadata debe ser un objeto")

        last_checked_at = payload.get("last_checked_at")
        return self.repositorio.guardar_fuente(
            FuenteCandidata(
                name=self._required_non_empty(payload, "name"),
                url=self._required_non_empty(payload, "url"),
                source_type=self._required_non_empty(payload, "source_type"),
                country=str(payload.get("country") or "").strip(),
                language=str(payload.get("language") or "").strip(),
                acquisition_method=self._required_non_empty(payload, "acquisition_method"),
                status=str(payload.get("status") or "CANDIDATE").strip() or "CANDIDATE",
                last_checked_at=self._parse_datetime(last_checked_at) if last_checked_at else None,
                notes=str(payload.get("notes") or ""),
                metadata=metadata,
            )
        )

    @staticmethod
    def _required_non_empty(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if value is None or str(value) == "":
            raise ValueError(f"{key} es obligatorio")
        return str(value)

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _stable_hash(source: str, source_url: str, raw_text: str) -> str:
        digest = hashlib.sha256(
            f"{source}\0{source_url}\0{raw_text}".encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest}"

