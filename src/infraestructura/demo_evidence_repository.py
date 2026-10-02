import hashlib
import json
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

from src.aplicacion.dto.oferta_dto import OfertaDTO
from src.aplicacion.procesador_ofertas import ProcesadorOfertas
from src.dominio.market_observation import MarketObservation
from src.dominio.servicios import ServicioCanonico
from src.infraestructura.sqlite.repositorio_sqlite_ofertas import RepositorioSQLiteOfertas


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "data/demo/evidence.json"
DEFAULT_DB = ROOT / "data/demo/demo.db"


def verified_captures(manifest_path: Path) -> tuple[dict, dict]:
    """Valida bytes guardados, rutas, identidad y fecha antes de interpretar."""
    manifest_path = Path(manifest_path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent.resolve()
    captures = {}
    for c in data["captures"]:
        path = (base / c["path"]).resolve()
        if not path.is_relative_to(base) or "fixtures" in path.parts:
            raise ValueError("La captura debe pertenecer al directorio de evidencia real.")
        if c["id"] in captures or not c.get("captured_at") or not c.get("source_url", "").startswith("https://"):
            raise ValueError("Procedencia inválida o captura duplicada.")
        datetime.fromisoformat(c["captured_at"])
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != c["sha256"]:
            raise ValueError("El hash de la captura no coincide.")
        captures[c["id"]] = {**c, "content":content, "text":" ".join(BeautifulSoup(content, "html.parser").stripped_strings)}
    ids = set()
    for row in data["observations"]:
        if row["id"] in ids:
            raise ValueError("Observación duplicada.")
        ids.add(row["id"])
        capture = captures.get(row["capture_id"])
        excerpt = " ".join(row.get("source_excerpt", "").split())
        if not capture or not excerpt or excerpt not in " ".join(capture["text"].split()):
            raise ValueError("La observación no está respaldada por la captura.")
        if row["price_raw"] not in excerpt or row["service_raw"] not in excerpt:
            raise ValueError("Precio o servicio sin respaldo textual.")
    return data, captures


def load_demo_evidence(manifest_path: Path = DEFAULT_MANIFEST, db_path: Path = DEFAULT_DB) -> list[MarketObservation]:
    data, captures = verified_captures(manifest_path)
    repo = RepositorioSQLiteOfertas(db_path)
    processor = ProcesadorOfertas(repositorio=repo)
    observations = []
    for row in data["observations"]:
        capture = captures[row["capture_id"]]
        observed_on = datetime.fromisoformat(capture["captured_at"]).date()
        dto = OfertaDTO(empresa_nombre=row["provider"], servicio_raw=row["service_raw"],
                       precio_raw=row["price_raw"], moneda=row["currency"] or "",
                       provincia=row["province"] or "", ciudad=row["city"] or "",
                       fuente=capture["source_url"], fecha_relevamiento=observed_on, modalidad=row["modality"])
        oferta = processor.procesar(dto)
        if oferta and row["currency"] is not None and oferta.moneda != row["currency"]:
            raise ValueError("La moneda declarada contradice el importe normalizado.")
        if oferta and (oferta.servicio == ServicioCanonico.DESCONOCIDO or oferta.servicio.value != row["service"]):
            oferta = None
        observations.append(MarketObservation(
            id=row["id"], oferta=oferta, provider=row["provider"], service=row["service"],
            currency=row["currency"], modality=row["modality"], unit=row["unit"], scope=row["scope"],
            province=row["province"], city=row["city"], source_url=capture["source_url"],
            captured_at=capture["captured_at"], effective_date=row["effective_date"], capture_id=row["capture_id"],
            raw={"servicio_raw":row["service_raw"], "precio_raw":row["price_raw"],
                 "source_excerpt":row["source_excerpt"]}, evidence_kind=row["evidence_kind"],
            comparability_established=row["comparability_established"],
            comparability_note=row.get("comparability_note")))
    return observations
