from fastapi.testclient import TestClient

from src.api.main import app


def test_catalogo_reusa_categorias_y_evidencia_real():
    r = TestClient(app).get("/market/catalog")
    assert r.status_code == 200
    data = r.json()
    assert {s["id"] for s in data["services"]} == {"malware","formateo","mantenimiento","soporte_redes","soporte_tecnico"}
    assert data["capture_count"] == 2
    assert "Villa de Mayo" in data["cities"]


def test_recorrido_real_offline_benchmark_precio_y_fuentes():
    client = TestClient(app)
    r = client.post("/market/query",json={"service":"soporte_tecnico"})
    assert r.status_code == 200
    data = r.json()
    assert data["provider_count"] == 2
    assert len(data["benchmarks"]) == 2
    first = data["benchmarks"][0]
    data = client.post("/market/query",json={"service":"soporte_tecnico","own_price":"35000,50",
        "own_currency":"ARS", "own_unit":first["unit"],"own_scope":first["scope"],
        "own_modality":first["modality"]}).json()
    assert data["benchmarks"][0]["own_price_difference_pct"] == "16.67"
    assert data["benchmarks"][1]["own_price_difference_pct"] is None
    offer = data["offers"][0]
    snapshot = client.get(offer["capture_url"])
    assert snapshot.status_code == 200
    assert "text/plain" in snapshot.headers["content-type"]
    assert offer["source_url"] in snapshot.text
    assert offer["captured_at"] in snapshot.text
    assert "sha256" in snapshot.text


def test_validaciones_estado_vacio_y_captura_inexistente():
    c = TestClient(app)
    assert c.post("/market/query",json={"service":"desconocido"}).status_code == 422
    assert c.post("/market/query",json={"service":"soporte_tecnico","own_price":"35000"}).status_code == 422
    assert c.post("/market/query",json={"service":"soporte_tecnico","own_price":"desde 35000",
        "own_unit":"hora","own_scope":"x","own_modality":"remoto"}).status_code == 422
    assert c.post("/market/query",json={"service":"soporte_redes"}).json()["offer_count"] == 0
    assert c.get("/market/captures/nonexistent").status_code == 404


def test_evidencia_corrupta_cierra_consulta_con_error_explicito(monkeypatch):
    import src.api.market as module
    def fail(): raise ValueError("hash inválido")
    monkeypatch.setattr(module,"load_demo_evidence",fail)
    r = TestClient(app).post("/market/query",json={"service":"soporte_tecnico"})
    assert r.status_code == 503
    assert "evidencia" in r.json()["detail"].lower()
