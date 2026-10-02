"""Verificación real del recorrido de la demo con Playwright en modo offline."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url",default="http://127.0.0.1:3000/mercado")
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright, expect

    out = Path(__file__).resolve().parents[1] / "docs/demo"
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={"width":1440,"height":1000},locale="es-AR")
        context.route("**/*",lambda route: route.continue_() if route.request.url.startswith(("http://127.0.0.1:","http://localhost:")) else route.abort())
        page=context.new_page()
        errors=[]
        page.on("pageerror",lambda error:errors.append(str(error)))
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
        assert not errors,errors
        report={"desktop":"1440x1000","mobile":"390x844","horizontal_overflow":False,
                "offline_external_requests_blocked":True,"page_errors":errors,
                "verified":["fuentes y captura","centavos y porcentaje","grupos separados",
                            "filtro geográfico","estado vacío","restablecer","precio inválido y reintento"]}
        (out / "verificacion-navegador.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(report,ensure_ascii=False))
        browser.close()


if __name__ == "__main__":
    main()
