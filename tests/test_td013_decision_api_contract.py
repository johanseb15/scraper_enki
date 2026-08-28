from src.api.main import app


def _decision_pricing_route():
    matches = [
        route
        for route in app.routes
        if getattr(route, "path", None)
        == "/decision/pricing"
        and "POST" in getattr(
            route,
            "methods",
            set(),
        )
    ]

    assert len(matches) == 1
    return matches[0]


def test_decision_pricing_has_explicit_response_model():
    route = _decision_pricing_route()

    assert route.response_model is not None


def test_decision_pricing_openapi_exposes_required_contract():
    schema = app.openapi()

    response_schema = (
        schema["paths"]
        ["/decision/pricing"]
        ["post"]
        ["responses"]
        ["200"]
        ["content"]
        ["application/json"]
        ["schema"]
    )

    assert "$ref" in response_schema

    component_name = response_schema["$ref"].split("/")[-1]
    component = schema["components"]["schemas"][component_name]

    required = set(
        component.get("required", [])
    )

    assert {
        "status",
        "headline",
        "summary",
        "parsed",
        "evidence",
        "market_resolution",
        "pricing_readiness",
        "evidence_probe",
    } <= required
