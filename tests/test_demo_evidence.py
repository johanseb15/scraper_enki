import hashlib
import importlib
import json
from pathlib import Path

import pytest

from src.normalizadores.normalizador_servicios import NormalizadorServicios
from src.dominio.servicios import ServicioCanonico


def test_conexion_remota_reutiliza_categoria_soporte_existente():
    assert NormalizadorServicios().normalizar("Conexión Remota x 1 HS - PC-Notebook-AIO") == ServicioCanonico.SOPORTE_TECNICO


def manifest(tmp_path):
    content = b"<html><p>Soporte tecnico 1.299,50</p></html>"
    (tmp_path / "public.html").write_bytes(content)
    data = {"captures": [{"id":"public", "path":"public.html", "sha256":hashlib.sha256(content).hexdigest(),
             "source_url":"https://provider.example/tarifa", "captured_at":"2026-10-02T14:00:00+00:00"}],
            "observations":[{"id":"public-1", "capture_id":"public", "provider":"Proveedor", "service":"soporte_tecnico",
                "service_raw":"Soporte tecnico", "price_raw":"1.299,50", "currency":"ARS", "modality":"remoto",
                "unit":"hora", "scope":"soporte general", "province":None,"city":None,
                "effective_date":None,"evidence_kind":"public_capture", "comparability_established":True,
                "source_excerpt":"Soporte tecnico 1.299,50"}]}
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(data),encoding="utf-8")
    return path, data


def load(path,tmp_path):
    return importlib.import_module("src.infraestructura.demo_evidence_repository").load_demo_evidence(path,tmp_path / "demo.db")


def test_captura_verificada_offline_e_importacion_idempotente(tmp_path):
    path,_ = manifest(tmp_path)
    first = load(path,tmp_path)
    second = load(path,tmp_path)
    assert len(first) == len(second) == 1
    assert first[0].oferta.precio_raw == "1.299,50"
    assert first[0].oferta.precio.valor.as_tuple().exponent == -2
    assert first[0].province is None
    assert first[0].effective_date is None


@pytest.mark.parametrize("defect",["hash","excerpt","traversal","fixture","duplicate","missing","currency"])
def test_no_admite_capturas_alteradas_o_sin_procedencia(tmp_path,defect):
    path,data = manifest(tmp_path)
    if defect == "hash": data["captures"][0]["sha256"] = "bad"
    if defect == "excerpt": data["observations"][0]["source_excerpt"] = "texto inventado"
    if defect == "traversal": data["captures"][0]["path"] = "../outside.html"
    if defect == "fixture": data["captures"][0]["path"] = "../../tests/fixtures/example.html"
    if defect == "duplicate": data["observations"].append(data["observations"][0])
    if defect == "missing": data["captures"][0]["captured_at"] = None
    if defect == "currency": data["observations"][0]["currency"] = "USD"
    path.write_text(json.dumps(data),encoding="utf-8")
    with pytest.raises(ValueError): load(path,tmp_path)
