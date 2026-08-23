import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
from src.aplicacion.pricing_cohort_loader import cargar_cohortes_pricing_runtime
from src.infraestructura.real_world_query_tracer import trace_real_world_query


ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)

API_CASES = {
    "A_HUMAN_REAL_QUERY": (
        "Cuánto puedo cobrar por formatear una notebook?",
        "CLARIFICATION_REQUIRED",
    ),
    "B_REMOTE_HOURLY_WITH_LOCATION": (
        "Me cobran 30000 por hora por soporte remoto en Córdoba",
        "CLARIFICATION_REQUIRED",
    ),
    "C_FORMAT_PC": (
        "Necesito formatear una PC",
        "CLARIFICATION_REQUIRED",
    ),
    "D_KNOWN_EVIDENCE": (
        "Cuánto se está cobrando por hora por soporte remoto?",
        "RANGE_READY",
    ),
    "E_UNSUPPORTED_BUNDLE": (
        "me cobran 110 lucas por formateo y backup en Córdoba",
        "UNSUPPORTED_QUERY",
    ),
    "TECHNICAL_NEED": (
        "Estoy instalando Windows 11 y se queda congelado en 10%. ¿Qué puede estar pasando?",
        "TECHNICAL_NEED_ROUTED",
    ),
}


def test_real_api_cases_have_schema_no_exception_and_trace_semantic_parity():
    local, remote = cargar_cohortes_pricing_runtime()
    protected = (
        ROOT / "data/field/human_real_cases_v1.jsonl",
        ROOT / "data/field/human_real_query_traces_v1.jsonl",
        ROOT / "data/knowledge_candidates_v1.jsonl",
        ROOT / "data/candidate_shadow_validation_results_v2.jsonl",
    )
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}

    for case_id, (query, expected_status) in API_CASES.items():
        response = CLIENT.post("/decision/pricing", json={"query": query})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == expected_status
        assert {"headline", "summary", "parsed", "evidence"} <= body.keys()

        trace = trace_real_world_query(
            query,
            local_cohortes=local,
            remote_cohortes=remote,
            source_case_id=f"e2e-api:{case_id}",
            case_origin="CURATED_ENKI",
        )
        assert trace.readiness == body["status"]
        assert trace.intent_result["action"] == body["parsed"]["intent_action"]
        assert trace.parser_result["canonical_services"] == body["parsed"]["canonical_services"]
        assert trace.runtime_mutation is False
        assert trace.promotion_authorized is False

    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected} == before


def test_current_real_cohorts_do_not_manufacture_decision_ready():
    response = CLIENT.post(
        "/decision/pricing",
        json={"query": "Cuánto se está cobrando por hora por soporte remoto?"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "RANGE_READY"
    assert response.json()["evidence"]["decision_label"] is None
