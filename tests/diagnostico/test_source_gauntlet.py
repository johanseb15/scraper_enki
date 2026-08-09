from src.infraestructura.diagnostico.source_gauntlet import (
    Dificultad,
    EstrategiaAdquisicion,
    analizar_html,
    comparar_senales,
)


def test_detecta_tabla_y_precios_en_html_estatico():
    html = """
        <html><head><title>Servicio Técnico Córdoba</title></head><body>
        <table><tr><th>Servicio</th><th>Precio</th></tr>
        <tr><td>Formateo de PC</td><td>ARS $ 25.000</td></tr></table>
        </body></html>
    """

    resultado = analizar_html(html, "https://ejemplo.test/servicios")

    assert resultado.tablas == 1
    assert resultado.precios_aproximados == 1
    assert resultado.muestras_precio_numerico == [25000]
    assert resultado.estrategia_sugerida is EstrategiaAdquisicion.HTTP_STATIC
    assert resultado.dificultad is Dificultad.A


def test_prefiere_datos_estructurados_cuando_hay_json_ld():
    html = """
        <script type="application/ld+json">
        {"@type":"Service","name":"Reparación de notebook",
         "offers":{"@type":"Offer","price":"35000","priceCurrency":"ARS"}}
        </script>
    """

    resultado = analizar_html(html, "https://ejemplo.test")

    assert resultado.json_ld == 1
    assert resultado.candidatos_raw[0]["nombre_raw"] == "Reparación de notebook"
    assert resultado.candidatos_raw[0]["precio_numerico_posible"] == 35000
    assert resultado.estrategia_sugerida is EstrategiaAdquisicion.WEB_STRUCTURED


def test_json_ld_de_navegacion_no_eleva_html_estatico_a_structured():
    html = """
        <script type="application/ld+json">
        {"@type":"BreadcrumbList","itemListElement":[
          {"@type":"ListItem","name":"Inicio","position":1}
        ]}
        </script>
        <article class="servicio"><h2>Formateo</h2><span>$ 30.000</span></article>
    """

    resultado = analizar_html(html, "https://ejemplo.test")

    assert resultado.json_ld == 1
    assert resultado.estrategia_sugerida is EstrategiaAdquisicion.HTTP_STATIC


def test_sugiere_browser_para_shell_spa_sin_contenido_comercial():
    scripts = "".join(f'<script src="/chunk-{i}.js"></script>' for i in range(16))
    html = f'<html><body><div id="root"></div>{scripts}</body></html>'

    resultado = analizar_html(html, "https://spa.test")

    assert "contenedor_app" in resultado.indicios_spa_js
    assert resultado.estrategia_sugerida is EstrategiaAdquisicion.WEB_BROWSER
    assert resultado.dificultad is Dificultad.D


def test_clasifica_challenge_sin_intentar_evasion():
    html = "<html><title>Just a moment...</title><div id='cf-chl-widget'>Verify you are human</div></html>"

    resultado = analizar_html(html, "https://protegido.test")

    assert resultado.challenge_antibot
    assert resultado.estrategia_sugerida is EstrategiaAdquisicion.BLOCKED
    assert resultado.dificultad is Dificultad.E


def test_clasifica_verificacion_de_trafico_como_bloqueo():
    html = """
        <html><title>Verificación de cuenta</title>
        <a href='/registration?registrationType=negative_traffic'>Continuar</a>
        </html>
    """

    resultado = analizar_html(html, "https://mercado.test/gz/account-verification")

    assert "traffic_verification" in resultado.challenge_antibot
    assert resultado.estrategia_sugerida is EstrategiaAdquisicion.BLOCKED


def test_recaptcha_de_formulario_no_bloquea_contenido_http_visible():
    html = """
        <html><title>Servicios informáticos</title><body>
        <article class='servicio'><h2>Soporte técnico</h2></article>
        <form><div class='g-recaptcha'></div></form>
        </body></html>
    """

    resultado = analizar_html(html, "https://servicios.test")

    assert "captcha_component" in resultado.challenge_antibot
    assert resultado.estrategia_sugerida is EstrategiaAdquisicion.HTTP_STATIC


def test_compara_informacion_aparecida_solo_tras_render():
    http = analizar_html("<html><div id='root'></div></html>", "https://spa.test")
    browser = analizar_html(
        "<html><article class='product'><h2>Notebook</h2><span>$ 500.000</span></article></html>",
        "https://spa.test",
    )

    diferencia = comparar_senales(http, browser)

    assert diferencia["items_extra"] >= 1
    assert diferencia["precios_extra"] == 1
    assert diferencia["muestras_precio_nuevas"] == ["$ 500.000"]
