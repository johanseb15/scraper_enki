"""Verificación real del recorrido de la demo con Playwright en modo offline."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


def verificar_cotizacion(page, context, base_url, out, expect):
    """Exercise quote corrections with HTTP responses from the real local API.

    The saved runtime cohorts for this validation are empty. No synthetic
    positive pricing response is installed here.
    """
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("soporte", "Cobro 35000 pesos por una hora de soporte técnico remoto en Argentina, ¿es razonable?",
         "UNSUPPORTED_QUERY", "SOPORTE_REMOTO", "ARS", 35000),
        ("usd", "Me cobran USD 100 por hora por soporte remoto a todo el país",
         "UNSUPPORTED_QUERY", "SOPORTE_REMOTO", "USD", 100),
        ("centavos", "Me cobran $35.000,50 por formatear una notebook en Córdoba",
         "NO_EVIDENCE", "FORMATEO_INSTALACION_SO", "ARS", 35000.5),
        ("ambigua", "Me cobran 100 por hora por soporte remoto a todo el país",
         "CLARIFICATION_REQUIRED", "SOPORTE_REMOTO", "UNKNOWN", 100),
        ("contradictoria", "Me cobran ARS 100 USD por hora por soporte remoto a todo el país",
         "CLARIFICATION_REQUIRED", "SOPORTE_REMOTO", "UNKNOWN", 100),
    ]
    labels = {
        "NO_EVIDENCE": "Sin evidencia comparable",
        "UNSUPPORTED_QUERY": "Fuera del alcance actual",
        "CLARIFICATION_REQUIRED": "Falta aclarar la consulta",
    }
    results = []
    for viewport_name, viewport in (
        ("escritorio", {"width": 1440, "height": 1000}),
        ("movil", {"width": 390, "height": 844}),
    ):
        page.set_viewport_size(viewport)
        for name, query, status, service, currency, value in cases:
            page.goto(base_url)
            intent = "Estoy por enviar una cotización" if name == "soporte" else "Recibí una propuesta"
            page.get_by_role("link", name=intent).click()
            page.wait_for_url("**/cotizacion?intent=*")
            expect(page.get_by_role("heading", name="Revisá un precio con evidencia real")).to_be_visible()
            field = page.get_by_label("Cotización a evaluar", exact=True)
            field.fill(query)
            expect(field).to_have_value(query)
            with page.expect_response(lambda response: "/decision/pricing" in response.url) as pending:
                page.get_by_role("button", name="Analizar").click()
            response = pending.value
            assert response.status == 200
            body = response.json()
            assert body["status"] == status, body
            assert body["parsed"]["canonical_services"] == [service], body
            assert body["parsed"]["price"]["currency"] == currency, body
            assert body["parsed"]["price"]["value"] == value, body
            expect(page.get_by_text("Esto es lo que Enki entendió.", exact=True)).to_be_visible()
            expect(page.get_by_text(labels[status], exact=True)).to_be_visible()
            expect(page.get_by_text(body["summary"], exact=True).first).to_be_visible()
            assert "UNKNOWN" not in page.locator("body").inner_text()
            assert "Estas propuestas no incluyen lo mismo." not in page.locator("body").inner_text()
            assert page.locator("html").evaluate("el=>el.scrollWidth <= innerWidth")

            if name == "centavos":
                expect(page.get_by_text("$35.000,50", exact=True).first).to_be_visible()
                page.screenshot(path=str(out / f"centavos-interpretacion-{viewport_name}.png"), full_page=True)
                page.get_by_role("button", name="Corregir consulta").click()
                expect(field).to_have_value(query)
                with page.expect_response(lambda response: "/decision/pricing" in response.url):
                    page.get_by_role("button", name="Analizar").click()
                expect(page.get_by_text("Esto es lo que Enki entendió.", exact=True)).to_be_visible()

            if status == "CLARIFICATION_REQUIRED":
                expect(page.get_by_role("button", name="Ver resultado")).to_have_count(0)
                expect(page.get_by_text(body["clarification_question"], exact=True).first).to_be_visible()
            else:
                page.get_by_role("button", name="Ver resultado").click()
                expect(page.get_by_role("heading", name=body["headline"], exact=True)).to_be_visible()
                expect(page.get_by_text(body["summary"], exact=True).first).to_be_visible()
                expect(page.get_by_text(labels[status], exact=True).last).to_be_visible()
                expect(page.get_by_role("region", name="Rango comparable de precios publicados")).to_have_count(0)
                if name == "centavos":
                    expect(page.get_by_text("$35.000,50", exact=True).first).to_be_visible()
                    assert "$35.001" not in page.locator("body").inner_text()
                    page.screenshot(path=str(out / f"centavos-resultado-{viewport_name}.png"), full_page=True)
                assert "Estas propuestas no incluyen lo mismo." not in page.locator("body").inner_text()
                assert page.locator("html").evaluate("el=>el.scrollWidth <= innerWidth")
            results.append({"viewport": viewport_name, "case": name, "response": body})

        # A connection failure keeps the input and supports retry through Analizar.
        page.goto(base_url + "/cotizacion?intent=received_quote")
        field = page.get_by_label("Cotización a evaluar", exact=True)
        field.fill(cases[2][1])
        failure_route = lambda route: route.abort()
        context.route("**/decision/pricing", failure_route)
        page.get_by_role("button", name="Analizar").click()
        expect(page.get_by_text("Failed to fetch", exact=False)).to_be_visible()
        expect(field).to_have_value(cases[2][1])
        context.unroute("**/decision/pricing", failure_route)
        page.get_by_role("button", name="Analizar").click()
        expect(page.get_by_text("Esto es lo que Enki entendió.", exact=True)).to_be_visible()
        expect(page.get_by_text("$35.000,50", exact=True).first).to_be_visible()
    report = {"real_api": True, "synthetic_responses": False, "cases": results,
              "connection_failure_and_retry": True, "horizontal_overflow": False}
    (out / "verificacion-cotizacion.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"real_api": True, "cases": len(results), "connection_failure_and_retry": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url",default="http://127.0.0.1:3000/mercado")
    parser.add_argument("--cotizacion-only", action="store_true", help="Verifica sólo Cotización contra las cohortes runtime guardadas vacías.")
    parser.add_argument("--api-url", help="URL de una API real en puerto aislado; redirige el transporte sin simular respuestas.")
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright, expect

    out = Path(__file__).resolve().parents[1] / "docs/demo"
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={"width":1440,"height":1000},locale="es-AR")
        context.route("**/*",lambda route: route.continue_() if route.request.url.startswith(("http://127.0.0.1:","http://localhost:")) else route.abort())
        if args.api_url:
            context.route("**/decision/pricing", lambda route: route.continue_(url=args.api_url.rstrip("/") + "/decision/pricing"))
        page=context.new_page()
        errors=[]
        page.on("pageerror",lambda error:errors.append(str(error)))
        parsed_url = urlsplit(args.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if args.cotizacion_only:
            report = verificar_cotizacion(page, context, base_url, out / "correcciones-cotizacion", expect)
            assert not errors, errors
            print(json.dumps({**report, "page_errors": errors}, ensure_ascii=False))
            browser.close()
            return
        page.goto(args.url)
        expect(page.get_by_role("heading",name="BairesCloud")).to_be_visible()
        expect(page.get_by_role("heading",name="Bitz Computación").first).to_be_visible()
        assert page.locator("html").evaluate("el=>el.scrollWidth <= innerWidth")
        page.screenshot(path=str(out / "demo-escritorio.png"))
        expect(page.get_by_label("Grupo comparable")).to_have_value("0")
        page.get_by_label("Tu precio").fill("35.000,50")
        page.get_by_role("button",name="Comparar mi precio",exact=True).click()
        expect(page.get_by_text("16,67% respecto de la mediana")).to_be_visible()
        page.get_by_role("heading",name="Compará el mismo alcance").scroll_into_view_if_needed()
        page.screenshot(path=str(out / "demo-benchmark-escritorio.png"))
        with context.expect_page() as popup:
            page.get_by_role("link",name="Abrir captura guardada",exact=True).first.click()
        capture=popup.value
        capture.wait_for_load_state()
        assert "sha256:" in capture.locator("body").inner_text()
        assert "https://bairescloud.ar/servicio-tecnico.php" in capture.locator("body").inner_text()
        capture.close()
        page.get_by_role("combobox",name="Servicio",exact=True).select_option("soporte_redes")
        page.get_by_role("button",name="Consultar evidencia",exact=True).click()
        expect(page.get_by_role("heading",name="Todavía no hay evidencia para esta consulta")).to_be_visible()
        page.get_by_role("button",name="Restablecer caso",exact=True).click()
        expect(page.get_by_role("heading",name="BairesCloud")).to_be_visible()
        expect(page.get_by_label("Tu precio")).to_have_value("")

        page.get_by_role("combobox",name="Ubicación publicada",exact=True).select_option("Villa de Mayo")
        page.get_by_role("button",name="Consultar evidencia",exact=True).click()
        expect(page.get_by_role("heading",name="BairesCloud")).to_have_count(0)
        expect(page.get_by_role("heading",name="Bitz Computación").first).to_be_visible()
        page.get_by_role("button",name="Restablecer caso",exact=True).click()
        expect(page.get_by_role("heading",name="BairesCloud")).to_be_visible()

        page.set_viewport_size({"width":390,"height":844})
        page.evaluate("window.scrollTo(0,0)")
        assert page.locator("html").evaluate("el=>el.scrollWidth <= innerWidth")
        page.screenshot(path=str(out / "demo-movil.png"))
        page.get_by_label("Grupo comparable").select_option("1")
        page.get_by_label("Tu precio").fill("35000,50")
        page.get_by_role("button",name="Comparar mi precio",exact=True).click()
        expect(page.get_by_text("-12,50% respecto de la mediana")).to_be_visible()
        page.get_by_role("heading",name="Compará el mismo alcance").scroll_into_view_if_needed()
        page.screenshot(path=str(out / "demo-benchmark-movil.png"))
        page.get_by_label("Tu precio").fill("Desde 35000")
        page.get_by_role("button",name="Comparar mi precio",exact=True).click()
        expect(page.get_by_role("alert")).to_be_visible()
        page.get_by_role("button",name="Reintentar").click()
        expect(page.get_by_role("heading",name="BairesCloud")).to_be_visible()
        quote_report = verificar_cotizacion(page, context, base_url, out / "correcciones-cotizacion", expect)
        assert not errors,errors
        report={"desktop":"1440x1000","mobile":"390x844","horizontal_overflow":False,
                "offline_external_requests_blocked":True,"page_errors":errors,"cotizacion":quote_report,
                "verified":["fuentes y captura","centavos y porcentaje","grupos separados",
                            "filtro geográfico","estado vacío","restablecer","precio inválido y reintento"]}
        (out / "verificacion-navegador.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(report,ensure_ascii=False))
        browser.close()


if __name__ == "__main__":
    main()
